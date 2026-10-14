import logging
import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# uvicorn's logger, so these lines show up in the server console
logger = logging.getLogger("uvicorn.error")

# Set S2_LOG_TRACEBACK=1 to print the full traceback for every S2 failure
# (very verbose under load; the one-line "cause" is usually enough).
LOG_TRACEBACK = os.getenv("S2_LOG_TRACEBACK", "0") == "1"

S2_BASE_URL = os.getenv("S2_BASE_URL")

if not S2_BASE_URL:
    raise RuntimeError("S2_BASE_URL is not set")

client: httpx.AsyncClient | None = None


async def start_s2_client():
    global client

    client = httpx.AsyncClient(
        base_url=f"{S2_BASE_URL}/s2",
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=4.0,
        ),
    )


async def close_s2_client():
    global client

    if client is not None:
        await client.aclose()
        client = None


def _fail(exc, status_code, message, method, path, headers=None):
    """Log the real cause, then raise a clean HTTP error that still names it."""
    cause = f"{type(exc).__name__}: {exc}".rstrip(": ")

    logger.error(
        "S2 %s %s failed -> %s | cause: %s", method, path, status_code, cause,
        exc_info=exc if LOG_TRACEBACK else None,
    )

    raise HTTPException(
        status_code=status_code,
        detail=f"{message} | {cause}",
        headers=headers,
    ) from exc


async def _request(method: str, path: str, data: dict | None = None):
    if client is None:
        raise RuntimeError("S2 HTTP client has not been started")

    attempts = 2 if method == "GET" else 1

    for attempt in range(attempts):
        try:
            response = await client.request(method, path, json=data)
            break
        except httpx.PoolTimeout as exc:
            _fail(exc, 503, "Service busy, try again shortly", method, path,
                  headers={"Retry-After": "1"})
        except httpx.TimeoutException as exc:
            _fail(exc, 504, "S2 timed out", method, path)
        except httpx.ConnectError as exc:
            _fail(exc, 503, "S2 unreachable", method, path)
        except (httpx.ReadError, httpx.RemoteProtocolError) as exc:
            logger.warning(
                "S2 %s %s connection dropped (%s), attempt %d of %d",
                method, path, type(exc).__name__, attempt + 1, attempts,
            )
            if attempt == attempts - 1:
                _fail(exc, 502, "S2 connection error", method, path)
        except httpx.TransportError as exc:
            _fail(exc, 502, "S2 connection error", method, path)

    if response.is_error:
        try:
            detail = response.json().get("detail", "S2 request failed")
        except ValueError:
            detail = "S2 request failed"

        raise HTTPException(
            status_code=response.status_code,
            detail=detail,
        )

    return response.json()


async def get(path: str):
    return await _request("GET", path)


async def post(path: str, data: dict):
    return await _request("POST", path, data)


async def patch(path: str, data: dict):
    return await _request("PATCH", path, data)


async def delete(path: str):
    return await _request("DELETE", path)