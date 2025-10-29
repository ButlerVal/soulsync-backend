from fastapi import WebSocket
import logging
from typing import Dict, List
import uuid
import json # For sending structured messages

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        # Store connections mapped by user_id
        # Each user can potentially have multiple connections (e.g., browser + app)
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID):
        """Accepts a new WebSocket connection and adds it to the user's list."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: uuid.UUID):
        """Removes a WebSocket connection from the user's list."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"WebSocket disconnected for user {user_id}.")
                # If last connection for user, remove user entry
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    logger.info(f"User {user_id} now fully disconnected.")
            else:
                 logger.warning(f"Attempted to disconnect a non-existent WebSocket for user {user_id}.")
        else:
             logger.warning(f"Attempted to disconnect WebSocket for non-connected user {user_id}.")


    async def send_personal_message(self, message: dict, user_id: uuid.UUID):
        """Sends a JSON message to all active connections for a specific user."""
        disconnected_sockets = []
        if user_id in self.active_connections:
            logger.info(f"Sending message to user {user_id} ({len(self.active_connections[user_id])} connections)")
            message_json = json.dumps(message) # Convert dict to JSON string
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception as e: # Catch potential connection errors
                    logger.warning(f"Failed to send message to a WebSocket for user {user_id}: {e}")
                    disconnected_sockets.append(connection)

            # Clean up connections that failed
            for socket in disconnected_sockets:
                 self.disconnect(socket, user_id)
        else:
             logger.info(f"User {user_id} not connected. Message not sent.")

    async def broadcast(self, message: str):
        """Sends a plain text message to ALL connected users (e.g., system announcements)."""
        logger.info(f"Broadcasting message: {message}")
        message_json = json.dumps({"type": "broadcast", "content": message})
        all_sockets = []
        users_to_cleanup = []

        # Gather all sockets first to avoid modifying dict during iteration
        for user_id, connections in self.active_connections.items():
            all_sockets.extend([(conn, user_id) for conn in connections])

        disconnected_sockets_info = []
        for connection, user_id in all_sockets:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed during broadcast to user {user_id}: {e}")
                disconnected_sockets_info.append((connection, user_id))

        # Clean up failed connections
        for socket, user_id in disconnected_sockets_info:
             self.disconnect(socket, user_id)


# Create a single instance of the manager to be used throughout the app
connection_manager = ConnectionManager()