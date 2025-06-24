"""create_integration_table

Revision ID: 243935d139fa
Revises: conv_persistence_001
Create Date: 2025-06-12 12:27:29.218419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '243935d139fa'
down_revision: Union[str, None] = 'conv_persistence_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create integration table
    op.create_table(
        'integration',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('ruleset_id', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('integration_type', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('priority', sa.Integer, nullable=False, default=100),
        sa.Column('configuration', sa.JSON, nullable=False, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        schema='public'
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_integration_ruleset',
        'integration', 'ruleset',
        ['ruleset_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='CASCADE'
    )
    
    # Add unique constraint for name per ruleset
    op.create_unique_constraint(
        'uq_integration_name_per_ruleset',
        'integration',
        ['ruleset_id', 'name'],
        schema='public'
    )
    
    # Create indexes for performance
    op.create_index('idx_integration_ruleset_id', 'integration', ['ruleset_id'], schema='public')
    op.create_index('idx_integration_type', 'integration', ['integration_type'], schema='public')
    op.create_index('idx_integration_active', 'integration', ['is_active'], schema='public')
    op.create_index('idx_integration_priority', 'integration', ['priority'], schema='public')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_integration_priority', 'integration', schema='public')
    op.drop_index('idx_integration_active', 'integration', schema='public')
    op.drop_index('idx_integration_type', 'integration', schema='public')
    op.drop_index('idx_integration_ruleset_id', 'integration', schema='public')
    
    # Drop unique constraint
    op.drop_constraint('uq_integration_name_per_ruleset', 'integration', schema='public')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_integration_ruleset', 'integration', schema='public')
    
    # Drop table
    op.drop_table('integration', schema='public')
