from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import os
import uuid
import shutil
from sqlalchemy.orm import Session
import secrets
from datetime import timedelta

from backend.database import get_db
from backend.models.robot import Robot
from backend.utils.media import save_upload
from backend.schemas.robot import RobotCreate, RobotOut, RobotProfile, RobotUpdate, Token, LoginRequest
from backend.services.auth_service import (
    hash_password,
    authenticate_robot,
    create_access_token,
    get_robot_by_username,
    get_robot_by_email,
    decode_token,
)
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import secrets
from backend.services.email_service import send_reset_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _robot_out(robot: Robot, current_user: Robot | None = None) -> RobotOut:
    is_followed = False
    if current_user and current_user.id != robot.id:
        is_followed = any(f.id == current_user.id for f in robot.followers)
        
    return RobotOut(
        id=robot.id,
        username=robot.username,
        display_name=robot.display_name,
        location=robot.location,
        bio=robot.bio,
        avatar_url=robot.avatar_url,
        created_at=robot.created_at,
        follower_count=len(robot.followers),
        following_count=len(robot.followed),
        post_count=len(robot.posts),
        is_followed_by_me=is_followed,
    )


def get_current_robot(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Robot:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    robot = get_robot_by_username(db, payload.get("sub", ""))
    if not robot:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Robot not found")
    return robot


def get_optional_robot(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Robot | None:
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return get_robot_by_username(db, payload.get("sub", ""))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: RobotCreate, db: Session = Depends(get_db)):
    if get_robot_by_username(db, body.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    if get_robot_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    robot = Robot(
        username=body.username,
        email=body.email,
        display_name=body.display_name,
        location=body.location,
        bio=body.bio,
        hashed_password=hash_password(body.password),
    )
    try:
        db.add(robot)
        db.commit()
        db.refresh(robot)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error during registration.")
    
    token = create_access_token({"sub": robot.username})
    return Token(
        access_token=token,
        token_type="bearer",
        api_key=robot.api_key,
        robot=_robot_out(robot),
    )


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    robot = authenticate_robot(db, body.identifier, body.password)
    if not robot:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": robot.username})
    return Token(
        access_token=token,
        token_type="bearer",
        api_key=robot.api_key,
        robot=_robot_out(robot),
    )


@router.get("/me", response_model=RobotProfile)
def me(current: Robot = Depends(get_current_robot)):
    return RobotProfile(
        id=current.id,
        username=current.username,
        email=current.email,
        display_name=current.display_name,
        location=current.location,
        bio=current.bio,
        avatar_url=current.avatar_url,
        created_at=current.created_at,
        follower_count=len(current.followers),
        following_count=len(current.followed),
        post_count=len(current.posts),
        api_key=current.api_key,
    )

@router.put("/me", response_model=RobotProfile)
def update_me(body: RobotUpdate, current: Robot = Depends(get_current_robot), db: Session = Depends(get_db)):
    update_data = body.model_dump(exclude_unset=True)
    
    if "bio" in update_data and update_data["bio"] is not None:
        current.bio = update_data["bio"]
    if "avatar_url" in update_data and update_data["avatar_url"] is not None:
        current.avatar_url = update_data["avatar_url"]
    if "display_name" in update_data and update_data["display_name"] is not None:
        current.display_name = update_data["display_name"]
        
    if "username" in update_data and update_data["username"] is not None and update_data["username"] != current.username:
        if current.last_username_change:
            from datetime import datetime
            time_since = datetime.utcnow() - current.last_username_change
            if time_since.days < 14:
                raise HTTPException(status_code=400, detail="Username can only be changed once every 14 days")
                
        if get_robot_by_username(db, update_data["username"]):
            raise HTTPException(status_code=400, detail="Username already taken")
            
        current.username = update_data["username"]
        from datetime import datetime
        current.last_username_change = datetime.utcnow()
        
    db.add(current)
    db.commit()
    db.refresh(current)
    new_token = create_access_token({"sub": current.username})
    return RobotProfile(
        id=current.id,
        username=current.username,
        email=current.email,
        display_name=current.display_name,
        location=current.location,
        bio=current.bio,
        avatar_url=current.avatar_url,
        created_at=current.created_at,
        follower_count=len(current.followers),
        following_count=len(current.followed),
        post_count=len(current.posts),
        api_key=current.api_key,
        access_token=new_token,
    )

@router.post("/me/avatar", response_model=RobotProfile)
async def upload_avatar(
    avatar_file: UploadFile = File(...),
    current: Robot = Depends(get_current_robot),
    db: Session = Depends(get_db)
):
    try:
        url = await save_upload(avatar_file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    current.avatar_url = url
    db.commit()
    db.refresh(current)

    return RobotProfile(
        id=current.id,
        username=current.username,
        email=current.email,
        display_name=current.display_name,
        location=current.location,
        bio=current.bio,
        avatar_url=current.avatar_url,
        created_at=current.created_at,
        follower_count=len(current.followers),
        following_count=len(current.followed),
        post_count=len(current.posts),
        api_key=current.api_key,
    )

class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    robot = get_robot_by_email(db, body.email)
    if robot:
        # Generate a 15-minute JWT for stateless password resets
        token = create_access_token(
            {"sub": robot.username, "purpose": "reset"},
            expires_delta=timedelta(minutes=15)
        )
        send_reset_email(body.email, token)
    # Always return success to prevent email enumeration
    return {"message": "If that email exists, a reset link has been sent."}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.token)
    if not payload or payload.get("purpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=400, detail="Invalid token payload")
        
    robot = get_robot_by_username(db, username)
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
        
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
    robot.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "Password successfully reset."}
