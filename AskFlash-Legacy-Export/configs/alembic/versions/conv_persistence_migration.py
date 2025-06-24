"""Add persistent conversation tables for Feature 4

Revision ID: conv_persistence_001
Revises: 1a062455208a
Create Date: 2024-12-10 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'conv_persistence_001'
down_revision = '1a062455208a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create conversation table ###
    op.create_table(
        'conversation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('authors_note', sa.Text(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['public.user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index(op.f('ix_public_conversation_conversation_id'), 'conversation', ['conversation_id'], unique=True, schema='public')
    op.create_index(op.f('ix_public_conversation_id'), 'conversation', ['id'], unique=False, schema='public')
    
    # ### Create conversation_message table ###
    op.create_table(
        'conversation_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('mode', sa.String(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('thinking_steps', sa.JSON(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['public.conversation.conversation_id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    op.create_index(op.f('ix_public_conversation_message_id'), 'conversation_message', ['id'], unique=False, schema='public')


def downgrade() -> None:
    # ### Drop tables ###
    op.drop_index(op.f('ix_public_conversation_message_id'), table_name='conversation_message', schema='public')
    op.drop_table('conversation_message', schema='public')
    op.drop_index(op.f('ix_public_conversation_id'), table_name='conversation', schema='public')
    op.drop_index(op.f('ix_public_conversation_conversation_id'), table_name='conversation', schema='public')
    op.drop_table('conversation', schema='public') 