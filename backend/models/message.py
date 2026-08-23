from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime

from backend.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    text_content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)

    sender = relationship("Robot", foreign_keys=[sender_id])
    receiver = relationship("Robot", foreign_keys=[receiver_id])
