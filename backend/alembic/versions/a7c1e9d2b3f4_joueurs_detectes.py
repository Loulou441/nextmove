"""Ajout des joueurs détectés et du joueur choisi sur matches

Revision ID: a7c1e9d2b3f4
Revises: 4b5d2fafb134
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a7c1e9d2b3f4'
down_revision: Union[str, Sequence[str], None] = '4b5d2fafb134'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches', sa.Column('players', sa.JSON(), nullable=True))
    op.add_column('matches', sa.Column('selected_player_index', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('matches', 'selected_player_index')
    op.drop_column('matches', 'players')