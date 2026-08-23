import secrets
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

from backend.database import Base

# Association table for robot follow relationships
followers_table = Table(
    "followers",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("robots.id"), primary_key=True),
    Column("followed_id", Integer, ForeignKey("robots.id"), primary_key=True),
)


class Robot(Base):
    __tablename__ = "robots"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    display_name = Column(String(128), nullable=False)
    location = Column(String(256), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(512), nullable=True)
    hashed_password = Column(String(256), nullable=False)
    api_key = Column(String(64), unique=True, index=True, nullable=False, default=lambda: secrets.token_hex(32))
    last_username_change = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="robot", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="robot", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="robot", cascade="all, delete-orphan")

    followed = relationship(
        "Robot",
        secondary=followers_table,
        primaryjoin=id == followers_table.c.follower_id,
        secondaryjoin=id == followers_table.c.followed_id,
        backref="followers",
    )
