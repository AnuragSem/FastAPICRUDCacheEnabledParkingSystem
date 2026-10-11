import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

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
            keepalive_expiry=5.0,
        ),
    )


async def close_s2_client():
    global client

    if client is not None:
        await client.aclose()
        client = None


async def _request(method: str, path: str, data: dict | None = None):
    if client is None:
        raise RuntimeError("S2 HTTP client has not been started")

    response = await client.request(
        method,
        path,
        json=data,
    )

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
