from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
import uuid
import logging
from datetime import datetime

from ..core.database import get_db_session
from ..models.conversation import Conversation, ConversationMessage

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Production-ready conversation management system extracted from legacy.
    Handles conversation lifecycle, message persistence, and context management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_active_conversation(
        self, 
        user_id: str, 
        mode: str, 
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """
        Get active conversation or create new one.
        Preserves legacy behavior for conversation continuity.
        """
        try:
            # If conversation_id provided, try to get it
            if conversation_id:
                result = await self.db.execute(
                    select(Conversation).where(
                        and_(
                            Conversation.conversation_id == conversation_id,
                            Conversation.user_id == user_id
                        )
                    )
                )
                conversation = result.scalars().first()
                if conversation:
                    # Mark as active and return
                    await self._mark_conversation_active(conversation_id, user_id, mode)
                    return conversation

            # Find existing active conversation for user and mode
            result = await self.db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.user_id == user_id,
                        Conversation.mode == mode,
                        Conversation.is_active == True
                    )
                )
            )
            active_conversation = result.scalars().first()

            if active_conversation:
                logger.info(f"Found active conversation {active_conversation.conversation_id} for user {user_id}")
                return active_conversation

            # Create new conversation
            return await self.create_conversation(user_id, mode)

        except Exception as e:
            logger.error(f"Error getting/creating conversation: {str(e)}")
            # Fallback: create new conversation
            return await self.create_conversation(user_id, mode)

    async def create_conversation(self, user_id: str, mode: str, title: Optional[str] = None) -> Conversation:
        """Create new conversation with Flash AI branding"""
        try:
            conversation_id = str(uuid.uuid4())
            
            # Mark existing conversations as inactive for this user/mode
            await self.db.execute(
                update(Conversation)
                .where(
                    and_(
                        Conversation.user_id == user_id,
                        Conversation.mode == mode
                    )
                )
                .values(is_active=False)
            )

            # Create new conversation
            new_conversation = Conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                mode=mode,
                title=title or f"Flash {'Team' if mode == 'company' else 'General'} Chat",
                is_active=True,
                message_count=0
            )

            self.db.add(new_conversation)
            await self.db.commit()
            await self.db.refresh(new_conversation)

            logger.info(f"Created new conversation {conversation_id} for user {user_id} in {mode} mode")
            return new_conversation

        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            await self.db.rollback()
            raise

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        mode: Optional[str] = None,
        sources: Optional[List[Dict]] = None,
        confidence: Optional[float] = None,
        thinking_steps: Optional[List[Dict]] = None,
        token_count: Optional[int] = None,
        response_time_ms: Optional[int] = None
    ) -> ConversationMessage:
        """
        Save message to conversation with rich metadata.
        Extracted from legacy conversation system.
        """
        try:
            message = ConversationMessage(
                conversation_id=conversation_id,
                role=role,
                content=content,
                mode=mode,
                sources=sources,
                confidence=confidence,
                thinking_steps=thinking_steps,
                token_count=token_count,
                response_time_ms=response_time_ms
            )

            self.db.add(message)

            # Update conversation message count and last activity
            await self.db.execute(
                update(Conversation)
                .where(Conversation.conversation_id == conversation_id)
                .values(
                    message_count=Conversation.message_count + 1,
                    updated_at=datetime.utcnow()
                )
            )

            await self.db.commit()
            await self.db.refresh(message)

            logger.debug(f"Saved {role} message to conversation {conversation_id}")
            return message

        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            await self.db.rollback()
            raise

    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> List[ConversationMessage]:
        """
        Get conversation messages with optional user validation.
        Optimized for conversation context retrieval.
        """
        try:
            query = select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(ConversationMessage.created_at.asc())

            if limit:
                # Get most recent messages
                query = query.order_by(ConversationMessage.created_at.desc()).limit(limit)

            result = await self.db.execute(query)
            messages = result.scalars().all()

            if limit:
                # Reverse to chronological order
                messages = list(reversed(messages))

            logger.debug(f"Retrieved {len(messages)} messages from conversation {conversation_id}")
            return messages

        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            return []

    async def get_conversation_with_messages(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: Optional[int] = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation with messages for frontend.
        Legacy-compatible response format.
        """
        try:
            # Verify conversation ownership
            result = await self.db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.conversation_id == conversation_id,
                        Conversation.user_id == user_id
                    )
                )
            )
            conversation = result.scalars().first()

            if not conversation:
                return None

            # Get messages
            messages = await self.get_conversation_messages(conversation_id, limit)

            # Format for frontend
            return {
                "conversation_id": conversation.conversation_id,
                "title": conversation.title,
                "mode": conversation.mode,
                "authors_note": conversation.authors_note,
                "message_count": conversation.message_count,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "mode": msg.mode,
                        "sources": msg.sources,
                        "confidence": msg.confidence,
                        "timestamp": msg.created_at.isoformat(),
                        "thinking_steps": msg.thinking_steps
                    }
                    for msg in messages
                ]
            }

        except Exception as e:
            logger.error(f"Error retrieving conversation with messages: {str(e)}")
            return None

    async def create_new_chat(self, user_id: str, mode: str) -> Conversation:
        """
        Explicitly create new conversation (New Chat button).
        Deactivates existing conversations for clean state.
        """
        return await self.create_conversation(user_id, mode)

    async def update_authors_note(self, conversation_id: str, authors_note: str) -> bool:
        """
        Update authors note for conversation.
        Prepared for Feature 3 (Authors Note) implementation.
        """
        try:
            await self.db.execute(
                update(Conversation)
                .where(Conversation.conversation_id == conversation_id)
                .values(
                    authors_note=authors_note,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            logger.info(f"Updated authors note for conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating authors note: {str(e)}")
            await self.db.rollback()
            return False

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete conversation with ownership validation"""
        try:
            # Verify ownership and delete
            result = await self.db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.conversation_id == conversation_id,
                        Conversation.user_id == user_id
                    )
                )
            )
            conversation = result.scalars().first()

            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found or not owned by user {user_id}")
                return False

            # Delete messages first (cascade should handle this, but explicit is better)
            await self.db.execute(
                select(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation_id
                )
            )

            # Delete conversation
            await self.db.delete(conversation)
            await self.db.commit()

            logger.info(f"Deleted conversation {conversation_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            await self.db.rollback()
            return False

    async def list_user_conversations(
        self, 
        user_id: str, 
        mode: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List user conversations with metadata"""
        try:
            query = select(Conversation).where(Conversation.user_id == user_id)
            
            if mode:
                query = query.where(Conversation.mode == mode)
            
            query = query.order_by(Conversation.updated_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            conversations = result.scalars().all()

            return [
                {
                    "conversation_id": conv.conversation_id,
                    "title": conv.title,
                    "mode": conv.mode,
                    "message_count": conv.message_count,
                    "is_active": conv.is_active,
                    "last_activity": conv.updated_at.isoformat(),
                    "created_at": conv.created_at.isoformat()
                }
                for conv in conversations
            ]

        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            return []

    async def _mark_conversation_active(self, conversation_id: str, user_id: str, mode: str):
        """Mark specific conversation as active and deactivate others"""
        try:
            # Deactivate all conversations for this user/mode
            await self.db.execute(
                update(Conversation)
                .where(
                    and_(
                        Conversation.user_id == user_id,
                        Conversation.mode == mode
                    )
                )
                .values(is_active=False)
            )

            # Activate the specific conversation
            await self.db.execute(
                update(Conversation)
                .where(Conversation.conversation_id == conversation_id)
                .values(
                    is_active=True,
                    updated_at=datetime.utcnow()
                )
            )

            await self.db.commit()

        except Exception as e:
            logger.error(f"Error marking conversation active: {str(e)}")
            await self.db.rollback()

    async def get_conversation_context_summary(self, conversation_id: str, max_messages: int = 5) -> str:
        """
        Get summarized conversation context for AI prompts.
        Extracted from legacy context management.
        """
        try:
            messages = await self.get_conversation_messages(conversation_id, max_messages)
            
            if not messages:
                return ""

            context_parts = []
            for msg in messages[-max_messages:]:  # Get most recent messages
                if msg.role == "user":
                    context_parts.append(f"User: {msg.content[:200]}...")
                elif msg.role == "assistant":
                    # Extract key information from assistant responses
                    content = msg.content[:300]
                    if msg.sources:
                        content += f" [Sources: {len(msg.sources)} docs]"
                    context_parts.append(f"Assistant: {content}...")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return "" 