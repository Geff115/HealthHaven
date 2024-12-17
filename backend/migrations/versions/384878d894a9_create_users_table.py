"""Create users table

Revision ID: 384878d894a9
Revises: 
Create Date: 2024-12-17 19:09:41.511655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '384878d894a9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('first_name', sa.String(length=40), nullable=False),
        sa.Column('last_name', sa.String(length=40), nullable=False),
        sa.Column('username', sa.String(length=40), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=40), unique=True),
        sa.Column('role', sa.String(length=40), nullable=False),
        sa.Column('city', sa.String(length=80), nullable=False),
        sa.Column('state', sa.String(length=40), nullable=False),
        sa.Column('country', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    # Drop the users table
    op.drop_table('users')
