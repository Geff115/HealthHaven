import aioredis
import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create Redis connection
redis = aioredis.from_url(REDIS_URL, decode_responses=True)