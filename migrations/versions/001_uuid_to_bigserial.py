"""Convert UUID primary keys to BIGSERIAL

Revision ID: 001_uuid_to_bigserial
Revises: 
Create Date: 2025-01-07 18:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_uuid_to_bigserial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Convert all UUID primary keys and foreign keys to BIGSERIAL/BIGINT.
    
    This migration assumes a fresh installation or that the existing data
    can be recreated. For production systems with existing data, a more
    complex migration strategy would be needed to preserve data relationships.
    
    WARNING: This migration will drop and recreate all tables, losing all data.
    Ensure you have proper backups before running in production.
    """
    
    # Drop all tables in correct order (respecting foreign key constraints)
    op.execute("DROP TABLE IF EXISTS mcp_tools CASCADE")
    op.execute("DROP TABLE IF EXISTS mcp_servers CASCADE") 
    op.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS messages CASCADE")
    op.execute("DROP TABLE IF EXISTS conversations CASCADE")
    op.execute("DROP TABLE IF EXISTS prompts CASCADE")
    op.execute("DROP TABLE IF EXISTS llm_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    
    # Create users table with BIGSERIAL primary key
    op.create_table('users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_superuser', 'users', ['is_superuser'])

    # Create documents table with BIGSERIAL primary key and BIGINT foreign key
    op.create_table('documents',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False, default=0),
        sa.Column('file_type', sa.Enum('pdf', 'docx', 'txt', 'md', 'rtf', 'html', 'other', name='filetype'), nullable=False, default='other'),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'deleted', name='filestatus'), nullable=False, default='pending'),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Add indexes for documents table
    op.create_index('idx_documents_owner_id', 'documents', ['owner_id'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_documents_file_type', 'documents', ['file_type'])
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_documents_updated_at', 'documents', ['updated_at'])
    op.create_index('idx_documents_owner_status', 'documents', ['owner_id', 'status'])
    op.create_index('idx_documents_owner_type', 'documents', ['owner_id', 'file_type'])
    op.create_index('idx_documents_owner_created', 'documents', ['owner_id', 'created_at'])
    op.create_index('idx_documents_status_created', 'documents', ['status', 'created_at'])
    op.create_index('idx_documents_title', 'documents', ['title'])
    op.create_index('idx_documents_filename', 'documents', ['filename'])

    # Create document_chunks table with BIGSERIAL primary key and BIGINT foreign key
    op.create_table('document_chunks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=True),
        sa.Column('end_offset', sa.Integer(), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Add indexes for document_chunks table
    op.create_index('idx_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_chunks_chunk_index', 'document_chunks', ['chunk_index'])
    op.create_index('idx_chunks_created_at', 'document_chunks', ['created_at'])
    op.create_index('idx_chunks_document_index', 'document_chunks', ['document_id', 'chunk_index'])
    op.create_index('idx_chunks_document_created', 'document_chunks', ['document_id', 'created_at'])
    op.create_index('idx_chunks_token_count', 'document_chunks', ['token_count'])
    op.create_index('idx_chunks_language', 'document_chunks', ['language'])
    op.create_index('idx_chunks_embedding_model', 'document_chunks', ['embedding_model'])

    # Create conversations table with BIGSERIAL primary key and BIGINT foreign key
    op.create_table('conversations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_active', 'conversations', ['is_active'])
    op.create_index('idx_conversations_title', 'conversations', ['title'])

    # Create messages table with BIGSERIAL primary key and BIGINT foreign key
    op.create_table('messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, default=0),
        sa.Column('conversation_id', sa.BigInteger(), nullable=False),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('tool_call_results', sa.JSON(), nullable=True),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_role', 'messages', ['role'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])

    # Create prompts table with BIGSERIAL primary key
    op.create_table('prompts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_prompts_default', 'prompts', ['is_default'])
    op.create_index('idx_prompts_active', 'prompts', ['is_active'])
    op.create_index('idx_prompts_usage_count', 'prompts', ['usage_count'])
    op.create_index('idx_prompts_last_used', 'prompts', ['last_used_at'])
    op.create_index('idx_prompts_category', 'prompts', ['category'])

    # Create llm_profiles table with BIGSERIAL primary key
    op.create_table('llm_profiles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_name', sa.Text(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_llm_profiles_default', 'llm_profiles', ['is_default'])
    op.create_index('idx_llm_profiles_active', 'llm_profiles', ['is_active'])
    op.create_index('idx_llm_profiles_usage_count', 'llm_profiles', ['usage_count'])
    op.create_index('idx_llm_profiles_last_used', 'llm_profiles', ['last_used_at'])

    # Create mcp_servers table with BIGSERIAL primary key
    op.create_table('mcp_servers',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transport', sa.String(length=50), nullable=False, default='http'),
        sa.Column('timeout', sa.Integer(), nullable=False, default=30),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_connected', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connection_errors', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create mcp_tools table with BIGSERIAL primary key and BIGINT foreign key
    op.create_table('mcp_tools',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('original_name', sa.String(length=100), nullable=False),
        sa.Column('server_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['server_id'], ['mcp_servers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_mcp_tools_server_id', 'mcp_tools', ['server_id'])
    op.create_index('idx_mcp_tools_enabled', 'mcp_tools', ['is_enabled'])
    op.create_index('idx_mcp_tools_usage_count', 'mcp_tools', ['usage_count'])
    op.create_index('idx_mcp_tools_last_used', 'mcp_tools', ['last_used_at'])


def downgrade() -> None:
    """
    Convert BIGSERIAL primary keys back to UUID.
    
    WARNING: This is a destructive operation that will drop all tables and recreate
    them with UUID primary keys. All data will be lost.
    """
    
    # Drop all tables in correct order (respecting foreign key constraints)
    op.execute("DROP TABLE IF EXISTS mcp_tools CASCADE")
    op.execute("DROP TABLE IF EXISTS mcp_servers CASCADE") 
    op.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS messages CASCADE")
    op.execute("DROP TABLE IF EXISTS conversations CASCADE")
    op.execute("DROP TABLE IF EXISTS prompts CASCADE")
    op.execute("DROP TABLE IF EXISTS llm_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    
    # This would recreate the original UUID-based tables
    # Implementation omitted as it would require the original schema definitions
    # In practice, you would either restore from backup or manually recreate
    # the original UUID-based schema if downgrade is needed
    pass