"""Etat initial du schema

Revision ID: 6c2d5b477eae
Revises: 
Create Date: 2026-09-26 20:43:49.382846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c2d5b477eae'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    État initial : toutes les tables existent déjà en base (créées via
    api/init_db.py avant la mise en place d'Alembic). Cette migration sert
    de point de départ neutre pour l'historique — rien à créer ici.
    """
    pass


def downgrade() -> None:
    """Rien à annuler — voir upgrade()."""
    pass