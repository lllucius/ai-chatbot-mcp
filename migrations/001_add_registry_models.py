"""
Registry Models Migration

This migration adds the new registry models for MCP servers, tools, prompts,
and LLM parameter profiles.

Revision ID: 001_add_registry_models
Revises: 
Create Date: 2025-07-23 03:40:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_add_registry_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create registry tables for MCP servers, tools, prompts, and LLM profiles."""
    
    # Create MCP servers table
    op.create_table(
        'mcp_servers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transport', sa.String(50), nullable=False, default='http'),
        sa.Column('timeout', sa.Integer(), nullable=False, default=30),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_connected', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connection_errors', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for MCP servers
    op.create_index('idx_mcp_servers_name', 'mcp_servers', ['name'])
    op.create_index('idx_mcp_servers_enabled', 'mcp_servers', ['is_enabled'])
    op.create_index('idx_mcp_servers_connected', 'mcp_servers', ['is_connected'])
    
    # Create MCP tools table
    op.create_table(
        'mcp_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('original_name', sa.String(100), nullable=False),
        sa.Column('server_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('average_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['server_id'], ['mcp_servers.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for MCP tools
    op.create_index('idx_mcp_tools_name', 'mcp_tools', ['name'])
    op.create_index('idx_mcp_tools_server_id', 'mcp_tools', ['server_id'])
    op.create_index('idx_mcp_tools_enabled', 'mcp_tools', ['is_enabled'])
    op.create_index('idx_mcp_tools_usage_count', 'mcp_tools', ['usage_count'])
    op.create_index('idx_mcp_tools_last_used', 'mcp_tools', ['last_used_at'])
    
    # Create prompts table
    op.create_table(
        'prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for prompts
    op.create_index('idx_prompts_name', 'prompts', ['name'])
    op.create_index('idx_prompts_default', 'prompts', ['is_default'])
    op.create_index('idx_prompts_active', 'prompts', ['is_active'])
    op.create_index('idx_prompts_usage_count', 'prompts', ['usage_count'])
    op.create_index('idx_prompts_last_used', 'prompts', ['last_used_at'])
    op.create_index('idx_prompts_category', 'prompts', ['category'])
    
    # Create LLM profiles table
    op.create_table(
        'llm_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        # LLM Parameters
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('top_p', sa.Float(), nullable=True),
        sa.Column('top_k', sa.Integer(), nullable=True),
        sa.Column('repeat_penalty', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('max_new_tokens', sa.Integer(), nullable=True),
        sa.Column('context_length', sa.Integer(), nullable=True),
        sa.Column('presence_penalty', sa.Float(), nullable=True),
        sa.Column('frequency_penalty', sa.Float(), nullable=True),
        sa.Column('stop', sa.JSON(), nullable=True),
        sa.Column('other_params', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for LLM profiles
    op.create_index('idx_llm_profiles_name', 'llm_profiles', ['name'])
    op.create_index('idx_llm_profiles_default', 'llm_profiles', ['is_default'])
    op.create_index('idx_llm_profiles_active', 'llm_profiles', ['is_active'])
    op.create_index('idx_llm_profiles_usage_count', 'llm_profiles', ['usage_count'])
    op.create_index('idx_llm_profiles_last_used', 'llm_profiles', ['last_used_at'])


def downgrade() -> None:
    """Drop all registry tables."""
    op.drop_table('llm_profiles')
    op.drop_table('mcp_tools')
    op.drop_table('prompts')
    op.drop_table('mcp_servers')