"""Add role and status enums to User

Revision ID: 6763b4772dc5
Revises: f6db257bff63
Create Date: 2025-01-04 00:33:51.226511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = '6763b4772dc5'
down_revision: Union[str, None] = 'f6db257bff63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Define PostgreSQL Enum types
userrole_enum = ENUM('USER', 'ADMIN', name='userrole', create_type=True)
userstatus_enum = ENUM('ACTIVE', 'INACTIVE', name='userstatus', create_type=True)


def upgrade() -> None:
    # Create Enum types in the database
    userrole_enum.create(op.get_bind(), checkfirst=True)
    userstatus_enum.create(op.get_bind(), checkfirst=True)

    # Add the `role` column using the `userrole` Enum
    op.add_column('users', sa.Column('role', userrole_enum, nullable=False, server_default='USER'))

    # Alter the `status` column to use the `userstatus` Enum with a CASE statement for value mapping
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN status TYPE userstatus
        USING (
            CASE
                WHEN status = 'active' THEN 'ACTIVE'
                WHEN status = 'inactive' THEN 'INACTIVE'
                ELSE NULL
            END::userstatus
        )
        """
    )

def downgrade() -> None:
    # Revert the `status` column to its previous type
    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN status TYPE VARCHAR(20)
        USING status::TEXT
        """
    )

    # Drop the `role` column
    op.drop_column('users', 'role')

    # Drop the Enum types from the database
    userrole_enum.drop(op.get_bind(), checkfirst=True)
    userstatus_enum.drop(op.get_bind(), checkfirst=True)
