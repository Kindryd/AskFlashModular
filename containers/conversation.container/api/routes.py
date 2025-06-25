from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from core.database import get_db, Conversation, Message, get_redis
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime

router = APIRouter()

# Pydantic models
class MessageCreate(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    token_count: int

class ConversationCreate(BaseModel):
    user_id: str
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: int

class ConversationWithMessages(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    messages: List[MessageResponse]

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    
    conversation = Conversation(
        id=conversation_id,
        user_id=conversation_data.user_id,
        title=conversation_data.title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        is_active=conversation.is_active,
        message_count=0
    )

@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation with all its messages"""
    # Get conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    message_responses = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            metadata=json.loads(msg.message_metadata) if msg.message_metadata else None,
            created_at=msg.created_at,
            token_count=msg.token_count
        )
        for msg in messages
    ]
    
    return ConversationWithMessages(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        is_active=conversation.is_active,
        messages=message_responses
    )

@router.get("/conversations/user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for a user"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()
    
    conversation_responses = []
    for conv in conversations:
        # Count messages
        msg_count_result = await db.execute(
            select(Message.id).where(Message.conversation_id == conv.id)
        )
        message_count = len(msg_count_result.scalars().all())
        
        conversation_responses.append(
            ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_active=conv.is_active,
                message_count=message_count
            )
        )
    
    return conversation_responses

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a conversation"""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create message
    message_id = str(uuid.uuid4())
    message = Message(
        id=message_id,
        conversation_id=conversation_id,
        role=message_data.role,
        content=message_data.content,
        message_metadata=json.dumps(message_data.metadata) if message_data.metadata else None,
        token_count=len(message_data.content.split())  # Simple token estimation
    )
    
    db.add(message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        metadata=json.loads(message.message_metadata) if message.message_metadata else None,
        created_at=message.created_at,
        token_count=message.token_count
    )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    # Delete messages first
    await db.execute(
        delete(Message).where(Message.conversation_id == conversation_id)
    )
    
    # Delete conversation
    result = await db.execute(
        delete(Conversation).where(Conversation.id == conversation_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.commit()
    return {"status": "deleted", "conversation_id": conversation_id}

@router.get("/stats")
async def get_conversation_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get conversation service statistics"""
    # Get conversation count
    conv_result = await db.execute(select(Conversation.id))
    conversation_count = len(conv_result.scalars().all())
    
    # Get message count
    msg_result = await db.execute(select(Message.id))
    message_count = len(msg_result.scalars().all())
    
    # Get active conversations
    active_result = await db.execute(
        select(Conversation.id).where(Conversation.is_active == True)
    )
    active_count = len(active_result.scalars().all())
    
    return {
        "total_conversations": conversation_count,
        "total_messages": message_count,
        "active_conversations": active_count,
        "service": "conversation",
        "status": "operational"
    } 