from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    robot = relationship("Robot", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")
    replies = relationship("Comment", backref="parent_comment", remote_side=[id], cascade="all, delete-orphan")
