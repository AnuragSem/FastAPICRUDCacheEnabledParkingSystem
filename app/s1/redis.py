import os

from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

if REDIS_HOST is None:
    raise RuntimeError("Redis host is not set")

redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)