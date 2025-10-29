import uuid
from pydantic import BaseModel
from datetime import datetime
from app.models.message import MessageTypeEnum # Import the enum

class MessageBase(BaseModel):
    message_type: MessageTypeEnum = MessageTypeEnum.text
    content: str | None = None
    media_url: str | None = None

class MessageCreate(BaseModel):
    # Used when sending a message via API/WebSocket
    content: str # Require content for text messages

class MessageRead(MessageBase):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True