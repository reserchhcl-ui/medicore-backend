from typing import List, Optional

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import User
from app.modules.chat.models import ChatMessage
from app.modules.chat.schemas import MessageCreate


async def create_chat_message(
    db: AsyncSession, 
    sender_id: int, 
    message_data: MessageCreate
) -> ChatMessage:
    """Save a new chat message to the database."""
    message = ChatMessage(
        sender_id=sender_id,
        recipient_id=message_data.recipient_id,
        content=message_data.content,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


async def get_chat_history(
    db: AsyncSession, 
    user_id: int, 
    other_user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[ChatMessage]:
    """Get conversation history between two users."""
    stmt = (
        select(ChatMessage)
        .where(
            or_(
                and_(ChatMessage.sender_id == user_id, ChatMessage.recipient_id == other_user_id),
                and_(ChatMessage.sender_id == other_user_id, ChatMessage.recipient_id == user_id)
            )
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    # Return in chronological order
    messages = list(result.scalars().all())
    return messages[::-1]


async def mark_messages_as_read(
    db: AsyncSession, 
    recipient_id: int, 
    sender_id: int
):
    """Mark all messages from sender to recipient as read."""
    from sqlalchemy import update
    stmt = (
        update(ChatMessage)
        .where(ChatMessage.sender_id == sender_id)
        .where(ChatMessage.recipient_id == recipient_id)
        .where(ChatMessage.is_read == False)
        .values(is_read=True)
    )
    await db.execute(stmt)


async def get_recent_conversations(db: AsyncSession, user_id: int) -> List[dict]:
    """
    Get a list of users the current user has chatted with,
    including the last message and unread count.
    """
    # This is a complex query to get unique partners and their last message
    # For a simple implementation, we'll fetch unique other_user_ids first
    
    # Subquery for messages where user is sender or recipient
    stmt = select(ChatMessage).where(
        or_(ChatMessage.sender_id == user_id, ChatMessage.recipient_id == user_id)
    ).order_by(ChatMessage.created_at.desc())
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    partners = {}
    for msg in messages:
        partner_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
        if partner_id is None: continue # Skip broadcasts for now
        
        if partner_id not in partners:
            partners[partner_id] = {
                "last_message": msg.content,
                "last_message_time": msg.created_at,
                "unread_count": 0
            }
        
        if msg.recipient_id == user_id and not msg.is_read:
            partners[partner_id]["unread_count"] += 1
            
    # Load user details for partners
    partner_list = []
    for partner_id, info in partners.items():
        user_result = await db.execute(select(User).where(User.id == partner_id))
        user = user_result.scalar_one_or_none()
        if user:
            partner_list.append({
                "user_id": user.id,
                "full_name": user.full_name,
                **info
            })
            
    return partner_list
