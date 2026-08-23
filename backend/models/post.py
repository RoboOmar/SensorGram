from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    caption = Column(Text, nullable=True)
    sensor_data = Column(JSON, nullable=True)   # arbitrary JSON blob: {temp, battery, gps, …}
    image_url = Column(String(512), nullable=True)
    video_url = Column(String(512), nullable=True)
    post_type = Column(String(32), default="sensor")  # sensor | status | alert
    created_at = Column(DateTime, default=datetime.utcnow)

    robot = relationship("Robot", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
