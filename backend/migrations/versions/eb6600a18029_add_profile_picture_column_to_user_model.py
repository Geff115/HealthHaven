"""Add profile_picture column to User model

Revision ID: eb6600a18029
Revises: 7c75d8db487d
Create Date: 2025-01-20 11:22:02.170251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb6600a18029'
down_revision: Union[str, None] = '7c75d8db487d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('profile_picture', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'profile_picture')
    # ### end Alembic commands ###
