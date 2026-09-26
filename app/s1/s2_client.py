import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

S2_BASE_URL = os.getenv("S2_BASE_URL")


async def get(path: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{S2_BASE_URL}/s2{path}"
        )

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "S2 request failed")
        )

    return response.json()


async def post(path: str, data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{S2_BASE_URL}/s2{path}",
            json=data
        )

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "S2 request failed")
        )

    return response.json()


async def patch(path: str, data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{S2_BASE_URL}/s2{path}",
            json=data
        )

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "S2 request failed")
        )

    return response.json()


async def delete(path: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{S2_BASE_URL}/s2{path}"
        )

    if response.is_error:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "S2 request failed")
        )

    return response.json()