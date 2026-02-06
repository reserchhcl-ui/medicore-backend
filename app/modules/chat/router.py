import json
from typing import List

from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, 
    Depends, HTTPException, Query, status
)
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db, async_session_maker
from app.core.security import get_current_user
from app.modules.auth.models import User
from app.modules.chat.manager import manager
from app.modules.chat.schemas import MessageCreate, MessageResponse, ChatPartnerResponse
from app.modules.chat import service


router = APIRouter(prefix="/chat", tags=["chat"])


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """Helper to validate JWT token for WebSocket handshake."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing subject")
        
        from app.modules.auth.service import get_user_by_id
        user = await get_user_by_id(db, int(user_id))
        if user is None:
            raise ValueError("User not found")
        return user
    except (JWTError, ValueError):
        raise ValueError("Invalid token")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time chat.
    Expects 'token' as a query parameter for authentication.
    """
    # Create a fresh DB session for the long-lived connection
    async with async_session_maker() as db:
        try:
            user = await get_user_from_token(token, db)
        except ValueError as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(websocket, user.id)
        
        try:
            while True:
                # Receive data from client
                data = await websocket.receive_text()
                try:
                    msg_json = json.loads(data)
                    msg_data = MessageCreate(**msg_json)
                    
                    # 1. Persist to DB
                    db_msg = await service.create_chat_message(db, user.id, msg_data)
                    await db.commit()
                    
                    # 2. Prepare response payload
                    response_payload = {
                        "id": db_msg.id,
                        "sender_id": user.id,
                        "sender_name": user.full_name,
                        "content": db_msg.content,
                        "recipient_id": db_msg.recipient_id,
                        "created_at": db_msg.created_at.isoformat()
                    }
                    
                    # 3. Deliver real-time
                    if db_msg.recipient_id:
                        # Private message
                        if manager.is_user_online(db_msg.recipient_id):
                            await manager.send_personal_message(response_payload, db_msg.recipient_id)
                        # Optional: notify sender that message was sent
                    else:
                        # Broadcast message
                        await manager.broadcast(response_payload)
                        
                except Exception as e:
                    # Log error and notify client of failure
                    await websocket.send_json({"error": "Invalid message format or server error"})
                    
        except WebSocketDisconnect:
            manager.disconnect(user.id)
        except Exception:
            manager.disconnect(user.id)
            await websocket.close()


@router.get("/history/{other_user_id}", response_model=List[MessageResponse])
async def get_history(
    other_user_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Load conversation history with a specific user."""
    messages = await service.get_chat_history(
        db, current_user.id, other_user_id, limit, offset
    )
    # Mark as read
    await service.mark_messages_as_read(db, current_user.id, other_user_id)
    await db.commit()
    
    return messages


@router.get("/conversations", response_model=List[ChatPartnerResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List recent conversations and unread counts."""
    conversations = await service.get_recent_conversations(db, current_user.id)
    
    # Enrich with online status
    for conv in conversations:
        conv["is_online"] = manager.is_user_online(conv["user_id"])
        
    return conversations
