"""Migrate ruleset configs to integrations table

Revision ID: migrate_ruleset_001
Revises: 243935d139fa
Create Date: 2025-06-18 17:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

# revision identifiers
revision = 'migrate_ruleset_001'
down_revision = '243935d139fa'
branch_labels = None
depends_on = None

def upgrade():
    """Migrate existing ruleset configs to integrations table"""
    
    # First, get existing rulesets with configs
    connection = op.get_bind()
    
    # Get rulesets that have config data
    result = connection.execute(text("""
        SELECT id, name, created_by_id, azure_devops_config, notion_config, github_config, dynatrace_config
        FROM public.ruleset 
        WHERE azure_devops_config IS NOT NULL 
           OR notion_config IS NOT NULL 
           OR github_config IS NOT NULL 
           OR dynatrace_config IS NOT NULL
    """))
    
    rulesets_with_configs = result.fetchall()
    
    # Create integrations for each config
    for ruleset in rulesets_with_configs:
        ruleset_id = ruleset[0]
        ruleset_name = ruleset[1]
        created_by_id = ruleset[2]
        azure_config = ruleset[3]
        notion_config = ruleset[4]
        github_config = ruleset[5]
        dynatrace_config = ruleset[6]
        
        integration_priority = 1
        
        # Azure DevOps integration
        if azure_config:
            connection.execute(text("""
                INSERT INTO public.integration 
                (name, integration_type, ruleset_id, is_active, priority, configuration, created_at, updated_at)
                VALUES 
                (:name, :type, :ruleset_id, :active, :priority, :config, NOW(), NOW())
            """), {
                'name': f'{ruleset_name} - Azure DevOps',
                'type': 'azure_devops',
                'ruleset_id': ruleset_id,
                'active': True,
                'priority': integration_priority,
                'config': json.dumps(azure_config)
            })
            integration_priority += 1
        
        # Notion integration
        if notion_config:
            connection.execute(text("""
                INSERT INTO public.integration 
                (name, integration_type, ruleset_id, is_active, priority, configuration, created_at, updated_at)
                VALUES 
                (:name, :type, :ruleset_id, :active, :priority, :config, NOW(), NOW())
            """), {
                'name': f'{ruleset_name} - Notion',
                'type': 'notion',
                'ruleset_id': ruleset_id,
                'active': True,
                'priority': integration_priority,
                'config': json.dumps(notion_config)
            })
            integration_priority += 1
        
        # GitHub integration  
        if github_config:
            connection.execute(text("""
                INSERT INTO public.integration 
                (name, integration_type, ruleset_id, is_active, priority, configuration, created_at, updated_at)
                VALUES 
                (:name, :type, :ruleset_id, :active, :priority, :config, NOW(), NOW())
            """), {
                'name': f'{ruleset_name} - GitHub',
                'type': 'github',
                'ruleset_id': ruleset_id,
                'active': True,
                'priority': integration_priority,
                'config': json.dumps(github_config)
            })
            integration_priority += 1
        
        # Dynatrace integration
        if dynatrace_config:
            connection.execute(text("""
                INSERT INTO public.integration 
                (name, integration_type, ruleset_id, is_active, priority, configuration, created_at, updated_at)
                VALUES 
                (:name, :type, :ruleset_id, :active, :priority, :config, NOW(), NOW())
            """), {
                'name': f'{ruleset_name} - Dynatrace',
                'type': 'dynatrace',
                'ruleset_id': ruleset_id,
                'active': True,
                'priority': integration_priority,
                'config': json.dumps(dynatrace_config)
            })
            integration_priority += 1
    
    # Drop old config columns
    op.drop_column('ruleset', 'azure_devops_config', schema='public')
    op.drop_column('ruleset', 'notion_config', schema='public')
    op.drop_column('ruleset', 'github_config', schema='public')
    op.drop_column('ruleset', 'dynatrace_config', schema='public')

def downgrade():
    """Restore old config columns (data will be lost)"""
    
    # Re-add old config columns
    op.add_column('ruleset', sa.Column('azure_devops_config', sa.JSON(), nullable=True), schema='public')
    op.add_column('ruleset', sa.Column('notion_config', sa.JSON(), nullable=True), schema='public')
    op.add_column('ruleset', sa.Column('github_config', sa.JSON(), nullable=True), schema='public')
    op.add_column('ruleset', sa.Column('dynatrace_config', sa.JSON(), nullable=True), schema='public')
    
    # Note: Integration data will not be migrated back to config columns
    # This would require a more complex migration to extract config data from integrations 