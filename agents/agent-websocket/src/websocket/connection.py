"""WebSocket Connection Manager."""

import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_counter: int = 0
        logger.info("ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        self.connection_counter += 1
        connection_id = f"conn_{self.connection_counter}"
        self.active_connections[connection_id] = websocket
        logger.info(f"New connection: {connection_id}. Total: {len(self.active_connections)}")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"Disconnected: {connection_id}. Total: {len(self.active_connections)}")
    
    async def send_message(self, connection_id: str, message: dict):
        """
        Send a JSON message to a specific connection.
        
        Args:
            connection_id: Connection ID
            message: Message to send (will be converted to JSON)
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
