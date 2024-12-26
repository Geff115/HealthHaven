from ...celery_app import celery_app
from datetime import datetime, timedelta
from pytz import timezone, utc


@celery_app.task
def send_reminder(appointment_id):
    """
    Task to send a reminder for an upcoming appointment.
    """
    from app.models.appointment import Appointment
    from app.models.user import User
    from app.models.base import SessionLocal

    with SessionLocal() as session:
        # Fetch the appointment
        appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return f"Appointment ID {appointment_id} not found."

        # Fetch the user's timezone
        user = session.query(User).filter(User.id == appointment.user_id).first()
        user_timezone = timezone(user.timezone) if user and user.timezone else utc

        # Convert appointment time to user's timezone
        utc_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time).replace(tzinfo=utc)
        local_dt = utc_dt.astimezone(user_timezone)

        # Log or send the reminder
        reminder_message = (
            f"Reminder: Your appointment with Doctor {appointment.doctor_id} "
            f"is scheduled on {local_dt.strftime('%Y-%m-%d')} at {local_dt.strftime('%H:%M')}."
        )
        print(reminder_message)

        return reminder_message
