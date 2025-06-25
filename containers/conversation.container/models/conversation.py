from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class TimestampMixin:
    """Mixin for automatic timestamp management"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Conversation(Base, TimestampMixin):
    """
    Conversation model extracted from legacy system.
    Supports persistent chat sessions with rich metadata.
    """
    __tablename__ = "conversation"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)  # Changed to String for flexibility
    mode = Column(String, nullable=False, default="company")  # 'company' or 'general'
    title = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    authors_note = Column(Text, nullable=True, default=None)  # Feature 3: Authors Note
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, nullable=True)  # For analytics

    # Relationship to messages
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if 'conversation_id' not in kwargs:
            kwargs['conversation_id'] = str(uuid.uuid4())
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Conversation(id={self.conversation_id}, user={self.user_id}, mode={self.mode})>"

class ConversationMessage(Base, TimestampMixin):
    """
    Conversation message model with rich metadata support.
    Supports thinking steps, sources, confidence scores, and performance metrics.
    """
    __tablename__ = "conversation_message"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey('public.conversation.conversation_id'), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    mode = Column(String, nullable=True)  # Mode when message was created
    
    # Rich metadata
    sources = Column(JSON, nullable=True)  # Documentation sources
    confidence = Column(Float, nullable=True)  # AI confidence score (0.0-1.0)
    thinking_steps = Column(JSON, nullable=True)  # Feature 7: Persistent thinking steps
    token_count = Column(Integer, nullable=True)  # For cost tracking
    response_time_ms = Column(Integer, nullable=True)  # Performance metrics

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation={self.conversation_id})>"

    def to_dict(self):
        """Convert message to dictionary for API responses"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "mode": self.mode,
            "sources": self.sources,
            "confidence": self.confidence,
            "thinking_steps": self.thinking_steps,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "token_count": self.token_count,
            "response_time_ms": self.response_time_ms
        } 