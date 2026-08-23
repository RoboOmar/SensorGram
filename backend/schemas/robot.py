from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RobotCreate(BaseModel):
    username: str
    email: str
    display_name: str
    password: str
    location: Optional[str] = None
    bio: Optional[str] = None


class RobotUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class RobotOut(BaseModel):
    id: int
    username: str
    display_name: str
    location: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    is_followed_by_me: bool = False

    model_config = {"from_attributes": True}


class RobotProfile(RobotOut):
    email: Optional[str] = None  # only returned to the owner
    api_key: Optional[str] = None  # only returned to the owner
    access_token: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    api_key: str
    robot: RobotOut


class LoginRequest(BaseModel):
    identifier: str
    password: str
