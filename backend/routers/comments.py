import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.comment import Comment
from backend.models.post import Post
from backend.models.robot import Robot
from backend.routers.auth import get_current_robot
from backend.schemas.post import CommentCreate, CommentOut
from backend.services import feed_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/comments", tags=["comments"])


@router.post("/{post_id}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(                          # ← must be async: create_task needs the event loop
    post_id: int,
    body: CommentCreate,
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not body.body or not body.body.strip():
        raise HTTPException(status_code=422, detail="Comment body cannot be empty")

    try:
        comment = Comment(robot_id=current.id, post_id=post_id, body=body.body.strip())
        db.add(comment)
        db.commit()
        db.refresh(comment)
    except Exception:
        logger.exception("DB error saving comment on post %s", post_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save comment. Please try again.")

    out = CommentOut(
        id=comment.id,
        robot_id=comment.robot_id,
        robot_username=current.username,
        robot_display_name=current.display_name,
        robot_avatar_url=current.avatar_url,
        body=comment.body,
        created_at=comment.created_at,
    )

    # Broadcast to SSE subscribers — failures here must never affect the HTTP response
    try:
        asyncio.create_task(
            feed_service.broadcast("new_comment", {"post_id": post_id, **out.model_dump(mode="json")})
        )
    except Exception:
        logger.warning("SSE broadcast failed for new_comment on post %s (non-fatal)", post_id)

    return out


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.robot_id != current.id:
        raise HTTPException(status_code=403, detail="Not your comment")
    try:
        db.delete(comment)
        db.commit()
    except Exception:
        logger.exception("DB error deleting comment %s", comment_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete comment.")
