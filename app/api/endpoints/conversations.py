from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db.session import get_db_session
from app.models.user import User
from app.schemas.conversation import ConversationRead
from app.schemas.message import MessageRead
from app.services.message_service import message_service
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("", response_model=List[ConversationRead])
async def get_user_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves a list of conversations for the current logged-in user.
    """
    conversations = await message_service.get_conversations_for_user(db, user_id=current_user.user_id)

    # Convert SQLAlchemy models to Pydantic schemas for response
    response_data = []
    for conv in conversations:
         participant_ids = [conv.user1_id, conv.user2_id]
         response_data.append(
             ConversationRead(
                 conversation_id=conv.conversation_id,
                 participant_ids=participant_ids,
                 last_message_at=conv.last_message_at,
                 created_at=conv.created_at
             )
         )
    return response_data

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100), # Add pagination
    offset: int = Query(0, ge=0)
):
    """
    Retrieves message history for a specific conversation.
    """
    # 1. Verify the conversation exists and the user is part of it
    conversation = await message_service.get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )

    if current_user.user_id not in [conversation.user1_id, conversation.user2_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this conversation."
        )

    # 2. Fetch messages using the service
    messages = await message_service.get_messages_for_conversation(
        db, conversation_id=conversation_id, limit=limit, offset=offset
    )

    # Pydantic will automatically convert the list of Message models to MessageRead schemas
    return messages