"""WebSocket manager for real-time updates."""
import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("websocket_manager")


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Map of review_id -> set of connected websockets
        self.review_connections: Dict[str, Set[WebSocket]] = {}
        # Map of user_id -> set of connected websockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # All active connections
        self.active_connections: Set[WebSocket] = set()
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        review_id: Optional[str] = None
    ) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: Optional user ID to subscribe to user-specific updates
            review_id: Optional review ID to subscribe to review updates
        """
        await websocket.accept()
        
        async with self._lock:
            self.active_connections.add(websocket)
            
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(websocket)
            
            if review_id:
                if review_id not in self.review_connections:
                    self.review_connections[review_id] = set()
                self.review_connections[review_id].add(websocket)
        
        logger.info(
            "websocket_connected",
            user_id=user_id,
            review_id=review_id,
            total_connections=len(self.active_connections)
        )
    
    async def disconnect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        review_id: Optional[str] = None
    ) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
            
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            if review_id and review_id in self.review_connections:
                self.review_connections[review_id].discard(websocket)
                if not self.review_connections[review_id]:
                    del self.review_connections[review_id]
        
        logger.info(
            "websocket_disconnected",
            user_id=user_id,
            review_id=review_id,
            total_connections=len(self.active_connections)
        )
    
    async def subscribe_to_review(
        self,
        websocket: WebSocket,
        review_id: str
    ) -> None:
        """Subscribe a connection to review updates."""
        async with self._lock:
            if review_id not in self.review_connections:
                self.review_connections[review_id] = set()
            self.review_connections[review_id].add(websocket)
    
    async def unsubscribe_from_review(
        self,
        websocket: WebSocket,
        review_id: str
    ) -> None:
        """Unsubscribe a connection from review updates."""
        async with self._lock:
            if review_id in self.review_connections:
                self.review_connections[review_id].discard(websocket)
    
    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket
    ) -> None:
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def broadcast_to_review(
        self,
        review_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all connections subscribed to a review."""
        if review_id not in self.review_connections:
            return
        
        message['timestamp'] = datetime.utcnow().isoformat()
        
        disconnected = set()
        for websocket in self.review_connections[review_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to review: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws, review_id=review_id)
    
    async def broadcast_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all connections for a user."""
        if user_id not in self.user_connections:
            return
        
        message['timestamp'] = datetime.utcnow().isoformat()
        
        disconnected = set()
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws, user_id=user_id)
    
    async def broadcast_all(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        message['timestamp'] = datetime.utcnow().isoformat()
        
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)


# Event types for review progress
class ReviewEvent:
    """Review event types for WebSocket messages."""
    REVIEW_STARTED = "review_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    VIOLATION_FOUND = "violation_found"
    REVIEW_PROGRESS = "review_progress"
    REVIEW_COMPLETED = "review_completed"
    REVIEW_FAILED = "review_failed"
    BEDROCK_CALL = "bedrock_call"


async def send_review_event(
    manager: "ConnectionManager",
    review_id: str,
    event_type: str,
    data: Dict[str, Any]
) -> None:
    """
    Send a review event to all subscribed clients.
    
    Args:
        manager: The connection manager
        review_id: The review ID
        event_type: Type of event (from ReviewEvent)
        data: Event data payload
    """
    message = {
        "type": event_type,
        "review_id": review_id,
        "data": data
    }
    await manager.broadcast_to_review(review_id, message)


# Singleton instance
ws_manager = ConnectionManager()
