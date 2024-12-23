"""Added a new column to the doctor model

Revision ID: 80d4c5eb5703
Revises: b0f8a606fb92
Create Date: 2024-12-24 00:06:34.435500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80d4c5eb5703'
down_revision: Union[str, None] = 'b0f8a606fb92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - adjusted manually ###

    # Add column to the doctors table first
    op.add_column('doctors', sa.Column('doctor_username', sa.String(), nullable=False))
    op.create_unique_constraint('uq_doctors_doctor_username', 'doctors', ['doctor_username'])

    # Add foreign key constraint to the users table
    op.create_foreign_key(
        'fk_doctors_doctor_username_users_username',
        'doctors',
        'users',
        ['doctor_username'],
        ['username'],
        ondelete='CASCADE'
    )

    # Add column to other tables
    op.add_column('appointments', sa.Column('doctor_username', sa.String(), nullable=False))
    op.create_foreign_key(
        'fk_appointments_doctor_username_doctors_doctor_username',
        'appointments',
        'doctors',
        ['doctor_username'],
        ['doctor_username'],
        ondelete='CASCADE'
    )

    op.add_column('medical_records', sa.Column('doctor_username', sa.String(), nullable=False))
    op.create_foreign_key(
        'fk_medical_records_doctor_username_doctors_doctor_username',
        'medical_records',
        'doctors',
        ['doctor_username'],
        ['doctor_username'],
        ondelete='CASCADE'
    )

    op.add_column('prescriptions', sa.Column('doctor_username', sa.String(), nullable=False))
    op.create_foreign_key(
        'fk_prescriptions_doctor_username_doctors_doctor_username',
        'prescriptions',
        'doctors',
        ['doctor_username'],
        ['doctor_username'],
        ondelete='CASCADE'
    )

    # Add column to users table
    op.add_column('users', sa.Column('dob', sa.String(length=40), nullable=False))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - adjusted manually ###

    # Drop added columns and constraints in reverse order
    op.drop_column('users', 'dob')

    op.drop_constraint(
        'fk_prescriptions_doctor_username_doctors_doctor_username',
        'prescriptions',
        type_='foreignkey'
    )
    op.drop_column('prescriptions', 'doctor_username')

    op.drop_constraint(
        'fk_medical_records_doctor_username_doctors_doctor_username',
        'medical_records',
        type_='foreignkey'
    )
    op.drop_column('medical_records', 'doctor_username')

    op.drop_constraint(
        'fk_appointments_doctor_username_doctors_doctor_username',
        'appointments',
        type_='foreignkey'
    )
    op.drop_column('appointments', 'doctor_username')

    op.drop_constraint(
        'fk_doctors_doctor_username_users_username',
        'doctors',
        type_='foreignkey'
    )
    op.drop_column('doctors', 'doctor_username')

    # ### end Alembic commands ###