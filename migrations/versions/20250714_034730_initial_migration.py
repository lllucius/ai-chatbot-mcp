"""Initial migration with metainfo columns

Revision ID: 20250714_034730
Revises: 
Create Date: 2025-07-14 03:47:30.000000

Generated on: 2025-07-14 03:47:30 UTC
Current User: lllucius
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

# revision identifiers, used by Alembic.
revision: str = '20250714_034730'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema with metainfo columns."""
    
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_superuser', 'users', ['is_superuser'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'])
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create documents table with metainfo column
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('processing_status', sa.String(length=20), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_owner_id', 'documents', ['owner_id'])
    op.create_index('idx_documents_status', 'documents', ['processing_status'])
    op.create_index('idx_documents_title', 'documents', ['title'])
    op.create_index('idx_documents_type', 'documents', ['file_type'])
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'])

    # Create conversations table with metainfo column
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversations_active', 'conversations', ['is_active'])
    op.create_index('idx_conversations_title', 'conversations', ['title'])
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index(op.f('ix_conversations_id'), 'conversations', ['id'])

    # Create document_chunks table with metainfo column
    op.create_table('document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('start_char', sa.Integer(), nullable=False),
        sa.Column('end_char', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_chunks_chunk_index', 'document_chunks', ['chunk_index'])
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_document_chunks_embedding', 'document_chunks', ['embedding'], 
                   postgresql_using='ivfflat')
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'])

    # Create messages table with metainfo column
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('tool_call_results', sa.JSON(), nullable=True),
        sa.Column('metainfo', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_role', 'messages', ['role'])
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_index('idx_messages_role', table_name='messages')
    op.drop_index('idx_messages_created_at', table_name='messages')
    op.drop_index('idx_messages_conversation_id', table_name='messages')
    op.drop_table('messages')
    
    op.drop_index(op.f('ix_document_chunks_id'), table_name='document_chunks')
    op.drop_index('idx_document_chunks_embedding', table_name='document_chunks')
    op.drop_index('idx_document_chunks_document_id', table_name='document_chunks')
    op.drop_index('idx_document_chunks_chunk_index', table_name='document_chunks')
    op.drop_table('document_chunks')
    
    op.drop_index(op.f('ix_conversations_id'), table_name='conversations')
    op.drop_index('idx_conversations_user_id', table_name='conversations')
    op.drop_index('idx_conversations_title', table_name='conversations')
    op.drop_index('idx_conversations_active', table_name='conversations')
    op.drop_table('conversations')
    
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_index('idx_documents_type', table_name='documents')
    op.drop_index('idx_documents_title', table_name='documents')
    op.drop_index('idx_documents_status', table_name='documents')
    op.drop_index('idx_documents_owner_id', table_name='documents')