"""Create leadstatus enum type

Revision ID: 9a1b2c3d4e5f
Revises: 8f4d2e5c8a9b
Create Date: 2026-04-03 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9a1b2c3d4e5f'
down_revision = '8f4d2e5c8a9b'
branch_labels = None
depends_on = None


def upgrade():
    # Create the enum type in the app schema if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE app.leadstatus AS ENUM (
                'NEW',
                'ENGAGED',
                'QUALIFIED',
                'CONTACTED',
                'CONVERTED',
                'ABANDONED'
            );
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """)


def downgrade():
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS app.leadstatus CASCADE;")
