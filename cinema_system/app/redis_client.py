import os
import redis
from dotenv import load_dotenv

load_dotenv()

redis_db = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
)