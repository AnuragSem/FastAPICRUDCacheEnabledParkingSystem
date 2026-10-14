# import asyncio
# import json
# import logging
# import os

# from dotenv import load_dotenv
# from redis.asyncio import BlockingConnectionPool, Redis
# from redis.exceptions import RedisError

# load_dotenv()

# logger = logging.getLogger("s1.redis")

# REDIS_HOST = os.getenv("REDIS_HOST")
# REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# if REDIS_HOST is None:
#     raise RuntimeError("Redis host is not set")

# pool = BlockingConnectionPool(
#     host=REDIS_HOST,
#     port=REDIS_PORT,
#     decode_responses=True,
#     max_connections=1000,
#     timeout=1.0,
#     socket_connect_timeout=1.0,
#     socket_timeout=1.0,
# )

# redis_client = Redis(connection_pool=pool)

# _REDIS_ERRORS = (RedisError, asyncio.TimeoutError)

# # key -> the one S2 fetch currently running for that key
# _inflight: dict[str, asyncio.Task] = {}


# async def cache_get(key):
#     try:
#         return await redis_client.get(key)
#     except _REDIS_ERRORS as exc:
#         logger.warning("Redis GET failed, treating as miss: %s", exc)
#         return None


# async def cache_set(key, value):
#     try:
#         await redis_client.set(key, value)
#     except _REDIS_ERRORS as exc:
#         logger.warning("Redis SET failed, skipping: %s", exc)


# async def cache_delete(*keys):
#     # also forget any in-flight fetch, so its (possibly old) result
#     # doesn't get written back to the cache after a write
#     for key in keys:
#         _inflight.pop(key, None)
#     try:
#         await redis_client.delete(*keys)
#     except _REDIS_ERRORS as exc:
#         logger.warning("Redis DELETE failed: %s", exc)


# async def _load(key, fetch):
#     me = asyncio.current_task()
#     value = await fetch()
#     if _inflight.get(key) is me:
#         await cache_set(key, json.dumps(value))
#     return value


# def _done(key, task):
#     if _inflight.get(key) is task:
#         del _inflight[key]
#     if not task.cancelled():
#         task.exception()  # mark as retrieved so asyncio doesn't warn


# async def cached_fetch(key, fetch):
#     cached = await cache_get(key)
#     if cached is not None:
#         return json.loads(cached)

#     task = _inflight.get(key)
#     if task is None:
#         task = asyncio.create_task(_load(key, fetch))
#         _inflight[key] = task
#         task.add_done_callback(lambda t, k=key: _done(k, t))

#     # shield: if one caller disconnects, the shared fetch keeps running
#     return await asyncio.shield(task)





##################################################################################


import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from redis.asyncio import BlockingConnectionPool, Redis
from redis.exceptions import RedisError

from app.s1 import cache_stats as stats

load_dotenv()

logger = logging.getLogger("s1.redis")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

if REDIS_HOST is None:
    raise RuntimeError("Redis host is not set")

pool = BlockingConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    max_connections=1000,
    timeout=1.0,
    socket_connect_timeout=5.0,
    socket_timeout=5.0,
)

redis_client = Redis(connection_pool=pool)

_REDIS_ERRORS = (RedisError, asyncio.TimeoutError)

# key -> the one S2 fetch currently running for that key
_inflight: dict[str, asyncio.Task] = {}


async def cache_get(key):
    try:
        return await redis_client.get(key)
    except _REDIS_ERRORS as exc:
        stats.record_redis_error("GET", exc)
        logger.warning("Redis GET failed, treating as miss: %s", exc)
        return None


async def cache_set(key, value):
    try:
        await redis_client.set(key, value)
    except _REDIS_ERRORS as exc:
        stats.record_redis_error("SET", exc)
        logger.warning("Redis SET failed, skipping: %s", exc)


async def cache_delete(*keys):
    # also forget any in-flight fetch, so its (possibly old) result
    # doesn't get written back to the cache after a write
    for key in keys:
        _inflight.pop(key, None)
    try:
        await redis_client.delete(*keys)
    except _REDIS_ERRORS as exc:
        stats.record_redis_error("DELETE", exc)
        logger.warning("Redis DELETE failed: %s", exc)


async def _load(key, fetch):
    me = asyncio.current_task()
    value = await fetch()
    if _inflight.get(key) is me:
        await cache_set(key, json.dumps(value))
    return value


def _done(key, task):
    if _inflight.get(key) is task:
        del _inflight[key]
    if not task.cancelled():
        task.exception()  # mark as retrieved so asyncio doesn't warn


async def cached_fetch(key, fetch):
    cached = await cache_get(key)
    if cached is not None:
        stats.record_hit(key)
        return json.loads(cached)

    stats.record_miss(key)

    task = _inflight.get(key)
    if task is None:
        stats.record_s2_fetch(key)
        task = asyncio.create_task(_load(key, fetch))
        _inflight[key] = task
        task.add_done_callback(lambda t, k=key: _done(k, t))
    else:
        stats.record_coalesced(key)

    # shield: if one caller disconnects, the shared fetch keeps running
    return await asyncio.shield(task)