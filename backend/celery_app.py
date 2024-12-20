from celery import Celery


# Configure the Celery app
celery_app = Celery(
    "health_haven",
    broker="redis://localhost:6379/0",  # Redis connection
    backend="redis://localhost:6379/0",  # For storing task results
)

# Celery configuration
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True
)