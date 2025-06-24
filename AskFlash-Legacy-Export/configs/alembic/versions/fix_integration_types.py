"""Fix integration types to match service expectations

Revision ID: fix_integration_001
Revises: migrate_ruleset_001
Create Date: 2025-06-18 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = 'fix_integration_001'
down_revision = 'migrate_ruleset_001'
branch_labels = None
depends_on = None

def upgrade():
    """Fix integration types to match what the documentation service expects"""
    
    connection = op.get_bind()
    
    # Update integration types to match service expectations
    connection.execute(text("""
        UPDATE public.integration 
        SET integration_type = 'azure_devops_wiki'
        WHERE integration_type = 'azure_devops'
    """))
    
    connection.execute(text("""
        UPDATE public.integration 
        SET integration_type = 'notion_database'
        WHERE integration_type = 'notion'
    """))
    
    connection.execute(text("""
        UPDATE public.integration 
        SET integration_type = 'github_repos'
        WHERE integration_type = 'github'
    """))

def downgrade():
    """Revert integration types to simplified names"""
    
    connection = op.get_bind()
    
    # Revert to simple types
    connection.execute(text("""
        UPDATE public.integration 
        SET integration_type = 'azure_devops'
        WHERE integration_type = 'azure_devops_wiki'
    """))
    
    connection.execute(text("""
        UPDATE public.integration 
        SET integration_type = 'notion'
        WHERE integration_type = 'notion_database'
    """))
    
    connection.execute(text("""
        UPDATE public.integration 
        SET integration_type = 'github'
        WHERE integration_type = 'github_repos'
    """)) 