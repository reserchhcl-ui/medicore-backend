from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self):
        # Dictionary mapping user_id to their active WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a new WebSocket connection and register it."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        """Remove a disconnected user from active connections."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific connected user."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast(self, message: dict):
        """Send a message to all connected users."""
        for connection in self.active_connections.values():
            await connection.send_json(message)

    def is_user_online(self, user_id: int) -> bool:
        """Check if a user has an active connection."""
        return user_id in self.active_connections


# Global manager instance
manager = ConnectionManager()
