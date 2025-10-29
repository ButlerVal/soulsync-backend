import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, update
from datetime import datetime, timezone

from app.models.conversation import Conversation
from app.models.message import Message, MessageTypeEnum
from app.schemas.message import MessageCreate # Use basic create schema for now
import logging

logger = logging.getLogger(__name__)

class MessageService:
    """Service for handling conversations and messages."""

    async def get_or_create_conversation(self, db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID) -> Conversation:
        """Finds an existing conversation or creates a new one between two users."""
        # Ensure user1_id < user2_id to have a consistent lookup order
        u1 = min(user1_id, user2_id)
        u2 = max(user1_id, user2_id)

        result = await db.execute(
            select(Conversation).where(
                and_(Conversation.user1_id == u1, Conversation.user2_id == u2)
            )
        )
        conversation = result.scalars().first()

        if not conversation:
            logger.info(f"Creating new conversation between {u1} and {u2}")
            conversation = Conversation(user1_id=u1, user2_id=u2, last_message_at=datetime.now(timezone.utc))
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        return conversation

    async def get_conversation_by_id(self, db: AsyncSession, conversation_id: uuid.UUID) -> Conversation | None:
         """Gets a conversation by its ID."""
         result = await db.execute(select(Conversation).where(Conversation.conversation_id == conversation_id))
         return result.scalars().first()


    async def create_message(self, db: AsyncSession, conversation_id: uuid.UUID, sender_id: uuid.UUID, message_in: MessageCreate) -> Message:
        """Creates and saves a new message, updates conversation timestamp."""
        logger.info(f"Creating message for conversation {conversation_id} from sender {sender_id}")
        new_message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            message_type=MessageTypeEnum.text, # Assuming text for now
            content=message_in.content
            # media_url would be set here for other types
        )
        db.add(new_message)

        # Update conversation's last_message_at timestamp
        await db.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(last_message_at=datetime.now(timezone.utc))
        )

        await db.commit()
        await db.refresh(new_message)
        logger.info(f"Message {new_message.message_id} created.")
        return new_message

    async def get_messages_for_conversation(self, db: AsyncSession, conversation_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[Message]:
            """Retrieves messages for a specific conversation, ordered by creation time."""
            logger.info(f"Fetching messages for conversation {conversation_id} (limit={limit}, offset={offset})")
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc()) # Get newest first
                .offset(offset)
                .limit(limit)
            )
            # --- FIX: Convert Sequence to list explicitly ---
            messages_sequence = result.scalars().all()
            messages_list = list(messages_sequence) # Convert to list
            # --- END FIX ---

            logger.info(f"Found {len(messages_list)} messages.")

            # Return in chronological order (oldest first) for display
            return messages_list[::-1] # Reverse the list
    
    async def get_conversations_for_user(self, db: AsyncSession, user_id: uuid.UUID) -> list[Conversation]:
        """Retrieves all conversations a user is part of, ordered by last message time."""
        logger.info(f"Fetching conversations for user {user_id}")
        result = await db.execute(
            select(Conversation)
            .where(
                or_(Conversation.user1_id == user_id, Conversation.user2_id == user_id)
            )
            .order_by(Conversation.last_message_at.desc().nulls_last()) # Show recent chats first
            # Consider adding pagination later (limit/offset)
        )
        conversations = result.scalars().all()
        logger.info(f"Found {len(conversations)} conversations for user {user_id}")
        return list(conversations) # Convert Sequence to list for type hint


# Create a single instance
message_service = MessageService()