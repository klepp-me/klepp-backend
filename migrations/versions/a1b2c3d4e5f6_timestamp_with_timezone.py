"""Add timezone to timestamp columns

Revision ID: a1b2c3d4e5f6
Revises: 39c1fdf365c0
Create Date: 2025-12-27 16:52:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '39c1fdf365c0'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'video',
        'uploaded_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        postgresql_using='uploaded_at AT TIME ZONE \'UTC\''
    )
    op.alter_column(
        'video',
        'expire_at',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        postgresql_using='expire_at AT TIME ZONE \'UTC\''
    )


def downgrade():
    op.alter_column(
        'video',
        'uploaded_at',
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True)
    )
    op.alter_column(
        'video',
        'expire_at',
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True)
    )
