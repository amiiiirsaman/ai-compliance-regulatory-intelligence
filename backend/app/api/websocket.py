"""WebSocket API endpoints for real-time updates."""
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import get_logger
from app.services.websocket import ws_manager, ReviewEvent

logger = get_logger("websocket_api")

router = APIRouter()


async def get_user_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id and token_type == "access":
            return user_id
    except JWTError:
        pass
    return None


@router.websocket("/reviews/{review_id}")
async def websocket_review_endpoint(
    websocket: WebSocket,
    review_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time review progress updates.
    
    Connect with: ws://localhost:8000/api/v1/ws/reviews/{review_id}?token=<jwt_token>
    
    Events received:
    - review_started: Review process has begun
    - agent_started: An agent has started processing
    - agent_completed: An agent has finished processing
    - agent_failed: An agent encountered an error
    - violation_found: A new violation was detected
    - review_progress: Progress update with percentage
    - review_completed: Review finished successfully
    - review_failed: Review failed with error
    - bedrock_call: AWS Bedrock API call was made
    """
    # Authenticate user
    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Connect and subscribe to review updates
    await ws_manager.connect(websocket, user_id=user_id, review_id=review_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "review_id": review_id,
            "message": "Successfully connected to review updates"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (ping/pong or subscription changes)
                data = await websocket.receive_json()
                
                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle subscription to additional reviews
                elif data.get("type") == "subscribe":
                    new_review_id = data.get("review_id")
                    if new_review_id:
                        await ws_manager.subscribe_to_review(websocket, new_review_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "review_id": new_review_id
                        })
                
                # Handle unsubscribe
                elif data.get("type") == "unsubscribe":
                    old_review_id = data.get("review_id")
                    if old_review_id:
                        await ws_manager.unsubscribe_from_review(websocket, old_review_id)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "review_id": old_review_id
                        })
                        
            except json.JSONDecodeError:
                # Ignore malformed messages
                pass
                
    except WebSocketDisconnect:
        logger.info(
            "websocket_disconnected",
            user_id=user_id,
            review_id=review_id
        )
    finally:
        await ws_manager.disconnect(websocket, user_id=user_id, review_id=review_id)


@router.websocket("/user")
async def websocket_user_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for user-wide updates (all reviews).
    
    Connect with: ws://localhost:8000/api/v1/ws/user?token=<jwt_token>
    
    Receives updates for all of the user's reviews.
    """
    # Authenticate user
    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Connect for user-wide updates
    await ws_manager.connect(websocket, user_id=user_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "Successfully connected to user updates"
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        logger.info("websocket_user_disconnected", user_id=user_id)
    finally:
        await ws_manager.disconnect(websocket, user_id=user_id)
