"""create table videos_dubbed

Revision ID: 746f5c6598a8
Revises: 
Create Date: 2026-05-06 20:40:15.264234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '746f5c6598a8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "videos_dubbed",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer),
        sa.Column("file_name", sa.String(255)),
        sa.Column("file_url", sa.String(255)),
        sa.Column("thumbnail_url", sa.String(255)),
        sa.Column("status", sa.String(25)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime)
    )


def downgrade():
    op.drop_table("videos_dubbed")
