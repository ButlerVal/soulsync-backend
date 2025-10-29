from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json
import uuid
from datetime import datetime # Import datetime

from app.core.websocket_manager import connection_manager
from app.api.deps import get_current_user # Use get_current_user for WS auth
from app.models.user import User
from app.services.message_service import message_service
from app.schemas.message import MessageCreate, MessageRead
# No longer needed: import services needed to save messages...

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = None # Get token from query parameter
):
    """
    Main WebSocket endpoint for real-time communication.
    Authenticates user, handles message saving and routing.
    """
    # --- Authentication and Session Setup ---
    from app.db.session import AsyncSessionLocal
    from app.api.deps import get_current_user # Re-import locally for clarity

    db_session: AsyncSession | None = None
    current_user: User | None = None

    if not token:
        await websocket.close(code=1008, reason="Token not provided")
        logger.warning("WebSocket connection attempt without token.")
        return

    try:
        db_session = AsyncSessionLocal()
        current_user = await get_current_user(db=db_session, token=token)
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        logger.error(f"WebSocket Auth failed for token: {token[:5]}... - Error: {e}", exc_info=False)
        if db_session: await db_session.close()
        return
    finally:
        if db_session and not current_user:
             await db_session.close()

    if not current_user:
         logger.error("WebSocket connection proceeded despite failed authentication check.")
         await websocket.close(code=1011, reason="Internal server error")
         if db_session: await db_session.close()
         return
    # --- End Authentication ---

    user_id = current_user.user_id
    await connection_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received raw data from user {user_id}: {data}") # Use debug level

            # --- Message Processing ---
            try:
                message_data = json.loads(data)
                msg_type = message_data.get("type")
                conv_id_str = message_data.get("conversation_id")
                content = message_data.get("content")

                # Handle Chat Messages
                if msg_type == "chat" and conv_id_str and content:
                    conv_id = uuid.UUID(conv_id_str)

                    if not db_session: # Should be available, but check
                         logger.error(f"DB session lost for user {user_id} in conversation {conv_id}")
                         await websocket.send_text(json.dumps({"error": "Internal server error"}))
                         continue

                    # 1. Verify user is part of this conversation
                    conversation = await message_service.get_conversation_by_id(db_session, conv_id)
                    if not conversation:
                        logger.warning(f"User {user_id} sent message to non-existent conversation {conv_id}")
                        await websocket.send_text(json.dumps({"error": "Conversation not found"}))
                        continue

                    if user_id not in [conversation.user1_id, conversation.user2_id]:
                        logger.warning(f"User {user_id} unauthorized for conversation {conv_id}.")
                        await websocket.send_text(json.dumps({"error": "Not authorized"}))
                        continue

                    # 2. Save the message to the database
                    message_create_schema = MessageCreate(content=content)
                    new_message = await message_service.create_message(
                        db=db_session,
                        conversation_id=conv_id,
                        sender_id=user_id,
                        message_in=message_create_schema
                    )
                    logger.info(f"Saved message {new_message.message_id} from {user_id} to conv {conv_id}")

                    # 3. Get the recipient's user_id
                    recipient_id = conversation.user2_id if conversation.user1_id == user_id else conversation.user1_id

                    # 4. Format the message for sending (Use MessageRead schema)
                    message_read_schema = MessageRead.model_validate(new_message)
                    formatted_msg_payload = {
                        "type": "new_message",
                        "data": message_read_schema.model_dump(mode='json')
                    }

                    # 5. Send the message to the recipient via connection_manager
                    await connection_manager.send_personal_message(formatted_msg_payload, recipient_id)
                    logger.info(f"Sent message {new_message.message_id} to recipient {recipient_id}")

                    # Optional: Send confirmation back to sender
                    await websocket.send_text(json.dumps({
                        "type": "message_sent_confirmation",
                        "message_id": str(new_message.message_id),
                        "conversation_id": str(conv_id),
                        "timestamp": new_message.created_at.isoformat()
                     }))

                # Handle other message types (e.g., typing indicators) later
                # elif msg_type == "typing_start":
                #     # ... get recipient_id ...
                #     await connection_manager.send_personal_message({"type": "typing_start", "user_id": str(user_id), "conversation_id": str(conv_id)}, recipient_id)
                # elif msg_type == "typing_stop":
                #     # ... get recipient_id ...
                #     await connection_manager.send_personal_message({"type": "typing_stop", "user_id": str(user_id), "conversation_id": str(conv_id)}, recipient_id)

                else:
                    logger.warning(f"Received invalid or unhandled message format from {user_id}: {message_data}")
                    await websocket.send_text(json.dumps({"error": "Invalid message format or type"}))
            # --- Error Handling ---
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message from {user_id}: {data}")
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
            except ValueError as ve: # Specifically catch UUID errors
                logger.warning(f"Received invalid UUID format from {user_id}: {data} - Error: {ve}")
                await websocket.send_text(json.dumps({"error": "Invalid conversation_id format"}))
            except Exception as e:
                 logger.error(f"Error processing message from {user_id}: {e}", exc_info=True)
                 await websocket.send_text(json.dumps({"error": "Error processing message"}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected gracefully for user {user_id}")
    except Exception as e:
        # Log unexpected errors during receive/send loop
        logger.error(f"Unexpected WebSocket error for user {user_id}: {e}", exc_info=True)
    finally:
         # Ensure disconnection and session closure on any exit
         connection_manager.disconnect(websocket, user_id)
         if db_session:
             await db_session.close()
             logger.debug(f"DB session closed for user {user_id} WebSocket.")