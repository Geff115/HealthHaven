"""initial migration

Revision ID: b1314292f5a5
Revises: 
Create Date: 2025-01-24 09:44:34.509883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1314292f5a5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=40), nullable=False),
    sa.Column('last_name', sa.String(length=40), nullable=False),
    sa.Column('dob', sa.Date(), nullable=False),
    sa.Column('username', sa.String(length=40), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=40), nullable=False),
    sa.Column('city', sa.String(length=80), nullable=False),
    sa.Column('state', sa.String(length=40), nullable=False),
    sa.Column('country', sa.String(length=40), nullable=False),
    sa.Column('profile_picture', sa.String(), nullable=True),
    sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', name='userstatus'), nullable=False),
    sa.Column('role', sa.Enum('USER', 'DOCTOR', 'DOCTOR_PENDING', 'ADMIN', name='userrole'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_city'), 'users', ['city'], unique=False)
    op.create_index(op.f('ix_users_country'), 'users', ['country'], unique=False)
    op.create_index(op.f('ix_users_first_name'), 'users', ['first_name'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_last_name'), 'users', ['last_name'], unique=False)
    op.create_index(op.f('ix_users_state'), 'users', ['state'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('doctors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(length=40), nullable=False),
    sa.Column('specialization', sa.String(length=80), nullable=False),
    sa.Column('license_number', sa.String(length=80), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='doctorstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_doctors_id'), 'doctors', ['id'], unique=False)
    op.create_index(op.f('ix_doctors_license_number'), 'doctors', ['license_number'], unique=True)
    op.create_index(op.f('ix_doctors_specialization'), 'doctors', ['specialization'], unique=False)
    op.create_table('appointments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('appointment_date', sa.Date(), nullable=False),
    sa.Column('appointment_time', sa.Time(), nullable=False),
    sa.Column('appointment_note', sa.String(length=255), nullable=False),
    sa.Column('status', postgresql.ENUM('SCHEDULED', 'COMPLETED', 'CANCELLED', name='appointment_status'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('doctor_id', 'appointment_date', 'appointment_time', name='uq_appointment_time')
    )
    op.create_index(op.f('ix_appointments_appointment_date'), 'appointments', ['appointment_date'], unique=False)
    op.create_index(op.f('ix_appointments_doctor_id'), 'appointments', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_appointments_id'), 'appointments', ['id'], unique=False)
    op.create_table('medical_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('record_date', sa.DateTime(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('diagnosis', sa.String(length=255), nullable=True),
    sa.Column('treatment_plan', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medical_records_diagnosis'), 'medical_records', ['diagnosis'], unique=False)
    op.create_index(op.f('ix_medical_records_doctor_id'), 'medical_records', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_medical_records_id'), 'medical_records', ['id'], unique=False)
    op.create_index(op.f('ix_medical_records_record_date'), 'medical_records', ['record_date'], unique=False)
    op.create_index(op.f('ix_medical_records_treatment_plan'), 'medical_records', ['treatment_plan'], unique=False)
    op.create_table('prescriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('medication_name', sa.String(length=80), nullable=False),
    sa.Column('dosage', sa.String(length=80), nullable=False),
    sa.Column('instructions', sa.String(length=255), nullable=False),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'DISCONTINUED', 'EXPIRED', name='prescription_status'), nullable=False),
    sa.Column('expiry_date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prescriptions_appointment_id'), 'prescriptions', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_prescriptions_doctor_id'), 'prescriptions', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_prescriptions_id'), 'prescriptions', ['id'], unique=False)
    op.create_table('symptoms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('appointment_id', sa.Integer(), nullable=False),
    sa.Column('symptom_name', sa.String(length=80), nullable=False),
    sa.Column('severity_level', sa.Enum('mild', 'moderate', 'severe', name='severity_level'), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_symptoms_appointment_id'), 'symptoms', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_symptoms_id'), 'symptoms', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_symptoms_id'), table_name='symptoms')
    op.drop_index(op.f('ix_symptoms_appointment_id'), table_name='symptoms')
    op.drop_table('symptoms')
    op.drop_index(op.f('ix_prescriptions_id'), table_name='prescriptions')
    op.drop_index(op.f('ix_prescriptions_doctor_id'), table_name='prescriptions')
    op.drop_index(op.f('ix_prescriptions_appointment_id'), table_name='prescriptions')
    op.drop_table('prescriptions')
    op.drop_index(op.f('ix_medical_records_treatment_plan'), table_name='medical_records')
    op.drop_index(op.f('ix_medical_records_record_date'), table_name='medical_records')
    op.drop_index(op.f('ix_medical_records_id'), table_name='medical_records')
    op.drop_index(op.f('ix_medical_records_doctor_id'), table_name='medical_records')
    op.drop_index(op.f('ix_medical_records_diagnosis'), table_name='medical_records')
    op.drop_table('medical_records')
    op.drop_index(op.f('ix_appointments_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_doctor_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_appointment_date'), table_name='appointments')
    op.drop_table('appointments')
    op.drop_index(op.f('ix_doctors_specialization'), table_name='doctors')
    op.drop_index(op.f('ix_doctors_license_number'), table_name='doctors')
    op.drop_index(op.f('ix_doctors_id'), table_name='doctors')
    op.drop_table('doctors')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_state'), table_name='users')
    op.drop_index(op.f('ix_users_last_name'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_first_name'), table_name='users')
    op.drop_index(op.f('ix_users_country'), table_name='users')
    op.drop_index(op.f('ix_users_city'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###