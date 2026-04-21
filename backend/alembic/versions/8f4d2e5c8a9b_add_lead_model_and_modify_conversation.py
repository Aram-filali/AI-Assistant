"""Add Lead model and modify Conversation for public chats

Revision ID: 8f4d2e5c8a9b
Revises: 32fccc8c7e18
Create Date: 2026-04-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8f4d2e5c8a9b'
down_revision = '32fccc8c7e18'  # ✨ Changed to follow the real last migration
branch_labels = None
depends_on = None


def upgrade():
    # Create Lead table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'ENGAGED', 'QUALIFIED', 'CONTACTED', 'CONVERTED', 'ABANDONED', name='leadstatus', schema='app'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('meta_data', postgresql.JSON(), nullable=False),
        sa.Column('contacted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['app.conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['app.knowledge_bases.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_lead_email'),
        schema='app'
    )
    
    # Create indexes
    op.create_index('ix_app_leads_email', 'leads', ['email'], schema='app')
    op.create_index('ix_app_leads_status', 'leads', ['status'], schema='app')
    op.create_index('ix_app_leads_created_at', 'leads', ['created_at'], schema='app')
    op.create_index('ix_app_leads_conversation_id', 'leads', ['conversation_id'], schema='app')
    
    # Modify Conversation table
    # 1. Make user_id nullable
    op.alter_column('conversations', 'user_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
        schema='app')
    
    # 2. Add lead_id column
    op.add_column('conversations',
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='app')
    
    # 3. Add session_id column
    op.add_column('conversations',
        sa.Column('session_id', sa.String(255), nullable=True),
        schema='app')
    
    # 4. Create indexes on new columns
    op.create_index('ix_app_conversations_lead_id', 'conversations', ['lead_id'], schema='app')
    op.create_index('ix_app_conversations_session_id', 'conversations', ['session_id'], schema='app')
    
    # 5. Add foreign key constraint for lead_id
    op.create_foreign_key(
        'fk_app_conversations_lead_id',
        'conversations', 'leads',
        ['lead_id'], ['id'],
        source_schema='app',
        referent_schema='app',
        ondelete='SET NULL'
    )


def downgrade():
    # Remove foreign key
    op.drop_constraint('fk_app_conversations_lead_id', 'conversations', type_='foreignkey', schema='app')
    
    # Remove indexes
    op.drop_index('ix_app_conversations_session_id', table_name='conversations', schema='app')
    op.drop_index('ix_app_conversations_lead_id', table_name='conversations', schema='app')
    
    # Drop columns
    op.drop_column('conversations', 'session_id', schema='app')
    op.drop_column('conversations', 'lead_id', schema='app')
    
    # Make user_id not nullable again
    op.alter_column('conversations', 'user_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
        schema='app')
    
    # Drop Lead table
    op.drop_index('ix_app_leads_conversation_id', table_name='leads', schema='app')
    op.drop_index('ix_app_leads_created_at', table_name='leads', schema='app')
    op.drop_index('ix_app_leads_status', table_name='leads', schema='app')
    op.drop_index('ix_app_leads_email', table_name='leads', schema='app')
    op.drop_table('leads', schema='app')
