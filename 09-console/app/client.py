"""HTTP-клиент консоли: ошибки сервисов превращаются в значения, а не в исключения."""
import asyncio

import httpx

from app import config

TRANSPORT = {"value": None}


def transport():
    return TRANSPORT["value"]


async def get_json(url: str, params: dict | None = None) -> dict | None:
    return await call("GET", url, params=params)


async def post_json(url: str, body: dict) -> dict | None:
    return await call("POST", url, json=body)


async def call(method: str, url: str, **kwargs) -> dict | None:
    return decode(await perform(url, method, kwargs))


async def perform(url: str, method: str, kwargs: dict):
    results = await asyncio.gather(send(url, method, kwargs), return_exceptions=True)
    return results[0]


async def send(url: str, method: str, kwargs: dict):
    async with httpx.AsyncClient(timeout=config.TIMEOUT, transport=transport()) as client:
        return await client.request(method, url, **kwargs)


def decode(result) -> dict | None:
    return result.json() if usable(result) else None


def usable(result) -> bool:
    return isinstance(result, httpx.Response) and result.status_code == 200
