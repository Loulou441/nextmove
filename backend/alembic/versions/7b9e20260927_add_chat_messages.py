"""Persist match coach conversations after the existing shared schema.

Revision ID: 7b9e20260927
Revises: 56822ee323a9
"""
from alembic import op
import sqlalchemy as sa

revision = "7b9e20260927"
down_revision = "56822ee323a9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("match_id", sa.UUID(as_uuid=False), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_chat_messages_match_id", "chat_messages", ["match_id"])


def downgrade():
    op.drop_index("ix_chat_messages_match_id", table_name="chat_messages")
    op.drop_table("chat_messages")
