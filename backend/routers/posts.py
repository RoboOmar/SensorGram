import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.post import Post
from backend.models.like import Like
from backend.models.robot import Robot
from backend.routers.auth import get_current_robot, get_optional_robot
from backend.schemas.post import PostCreate, PostOut, CommentOut
from backend.services import feed_service
from backend.services.auth_service import get_robot_by_api_key
from backend.utils.media import save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _coerce_sensor_data(raw) -> Optional[dict]:
    """
    Safely coerce whatever is stored in the JSON column into a dict.
    - If it's already a dict: return it.
    - If it's a JSON string: parse it and return if it's a dict.
    - If it's anything else (int, list, None…): return None so the feed never crashes.
    """
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, ValueError):
            return None
    # scalar (int, float, bool, list…) — not a valid sensor dict
    return None


def _serialize_comment(c) -> CommentOut:
    return CommentOut(
        id=c.id,
        robot_id=c.robot_id,
        robot_username=c.robot.username,
        robot_display_name=c.robot.display_name,
        robot_avatar_url=c.robot.avatar_url,
        body=c.body,
        created_at=c.created_at,
    )


def _serialize_post(post: Post, current: Optional[Robot] = None) -> PostOut:
    """Serialize a Post ORM object to PostOut. Never raises — bad data is coerced gracefully."""
    liked = False
    if current:
        liked = any(lk.robot_id == current.id for lk in post.likes)

    return PostOut(
        id=post.id,
        robot_id=post.robot_id,
        robot_username=post.robot.username,
        robot_display_name=post.robot.display_name,
        robot_avatar_url=post.robot.avatar_url,
        caption=post.caption,
        sensor_data=_coerce_sensor_data(post.sensor_data),  # ← safe coercion
        image_url=post.image_url,
        video_url=post.video_url,
        post_type=post.post_type,
        like_count=len(post.likes),
        comment_count=len(post.comments),
        comments=[_serialize_comment(c) for c in post.comments],
        created_at=post.created_at,
        liked_by_me=liked,
    )


# ── API-key dependency (for robots posting programmatically) ──────────────────

def get_robot_by_key(
    x_robot_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[Robot]:
    if x_robot_key:
        return get_robot_by_api_key(db, x_robot_key)
    return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[PostOut])
def get_feed(
    skip: int = 0,
    limit: int = 20,
    current: Optional[Robot] = Depends(get_optional_robot),
    db: Session = Depends(get_db),
):
    try:
        posts = (
            db.query(Post)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        result = []
        for p in posts:
            try:
                result.append(_serialize_post(p, current))
            except Exception as e:
                # A single bad post must not kill the entire feed
                logger.warning("Skipping post id=%s during feed serialization: %s", p.id, e)
        return result
    except Exception as e:
        logger.exception("Unexpected error building feed")
        raise HTTPException(status_code=500, detail="Failed to load feed. Please try again.")


@router.get("/robot/{username}", response_model=list[PostOut])
def get_robot_posts(
    username: str,
    skip: int = 0,
    limit: int = 20,
    current: Optional[Robot] = Depends(get_optional_robot),
    db: Session = Depends(get_db),
):
    robot = db.query(Robot).filter(Robot.username == username).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    try:
        posts = (
            db.query(Post)
            .filter(Post.robot_id == robot.id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        result = []
        for p in posts:
            try:
                result.append(_serialize_post(p, current))
            except Exception as e:
                logger.warning("Skipping post id=%s for robot %s: %s", p.id, username, e)
        return result
    except Exception as e:
        logger.exception("Unexpected error loading posts for robot %s", username)
        raise HTTPException(status_code=500, detail="Failed to load posts. Please try again.")


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    caption: Optional[str] = Form(default=None),
    sensor_data: Optional[str] = Form(default=None),
    post_type: str = Form(default="sensor"),
    image: Optional[UploadFile] = File(default=None),
    image_url_str: Optional[str] = Form(default=None),
    video_url_str: Optional[str] = Form(default=None),
    current_jwt: Optional[Robot] = Depends(get_optional_robot),
    current_key: Optional[Robot] = Depends(get_robot_by_key),
    db: Session = Depends(get_db),
):
    current = current_jwt or current_key
    if not current:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # ── Image upload ──────────────────────────────────────────────────────
        image_url = None
        if image and image.filename:
            try:
                image_url = await save_upload(image)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
        elif image_url_str:
            image_url = image_url_str

        # ── Sensor data validation ────────────────────────────────────────────
        sensor_json = None
        if sensor_data and sensor_data.strip():
            try:
                parsed = json.loads(sensor_data)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=422,
                    detail="sensor_data must be valid JSON (e.g. {\"temperature\": 72.4})"
                )
            if not isinstance(parsed, dict):
                raise HTTPException(
                    status_code=422,
                    detail="sensor_data must be a JSON object (dict), not a scalar or array"
                )
            sensor_json = parsed

        # ── Persist post ──────────────────────────────────────────────────────
        post = Post(
            robot_id=current.id,
            caption=caption,
            sensor_data=sensor_json,
            image_url=image_url,
            video_url=video_url_str,
            post_type=post_type,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        # ── Serialize & broadcast ─────────────────────────────────────────────
        out = _serialize_post(post, current)
        import asyncio
        asyncio.create_task(feed_service.broadcast("new_post", out.model_dump(mode="json")))
        return out

    except HTTPException:
        raise  # re-raise our own HTTP errors as-is
    except Exception as e:
        logger.exception("Unexpected error creating post for robot %s", current.username)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create post. Please check your input and try again."
        )


@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def toggle_like(
    post_id: int,
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        existing = db.query(Like).filter(Like.robot_id == current.id, Like.post_id == post_id).first()
        if existing:
            db.delete(existing)
        else:
            db.add(Like(robot_id=current.id, post_id=post_id))
        db.commit()
    except Exception as e:
        logger.exception("Error toggling like on post %s", post_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update like.")


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.robot_id != current.id:
        raise HTTPException(status_code=403, detail="Not your post")
    try:
        db.delete(post)
        db.commit()
    except Exception as e:
        logger.exception("Error deleting post %s", post_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete post.")
