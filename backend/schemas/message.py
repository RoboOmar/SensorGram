from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    receiver_id: int
    text_content: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    text_content: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True
