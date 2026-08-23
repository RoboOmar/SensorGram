from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PostCreate(BaseModel):
    caption: Optional[str] = None
    sensor_data: Optional[Dict[str, Any]] = None
    post_type: str = "sensor"


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: int
    robot_id: int
    robot_username: str
    robot_display_name: str
    robot_avatar_url: Optional[str]
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    id: int
    robot_id: int
    robot_username: str
    robot_display_name: str
    robot_avatar_url: Optional[str]
    caption: Optional[str]
    sensor_data: Optional[Dict[str, Any]]
    image_url: Optional[str]
    video_url: Optional[str]
    post_type: str
    like_count: int = 0
    comment_count: int = 0
    comments: List[CommentOut] = []
    created_at: datetime
    liked_by_me: bool = False

    model_config = {"from_attributes": True}
