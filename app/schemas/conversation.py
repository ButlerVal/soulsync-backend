import uuid
from pydantic import BaseModel
from datetime import datetime
from app.schemas.user import UserRead # To show participant details

class ConversationRead(BaseModel):
    conversation_id: uuid.UUID
    # Maybe include simplified participant info
    # user1: UserRead
    # user2: UserRead
    participant_ids: list[uuid.UUID] # Simple list of user IDs involved
    last_message_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True