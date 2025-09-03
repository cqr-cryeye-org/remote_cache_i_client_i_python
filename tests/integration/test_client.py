import os

import aiohttp
import pytest
from dotenv import load_dotenv
from pydantic import BaseModel, HttpUrl

from remote_cache_client import RemoteCacheClient


class CacheableModel(BaseModel):
    parameter: str


async def make_action(
    data: CacheableModel,
    client_for_action: aiohttp.ClientSession,
) -> str:
    async with client_for_action.get("https://example.com") as resp:
        await resp.text()  # Just to show that we can use the client here
        return data.parameter[::-1]  # Just an example action


async def example(
    cache_client: RemoteCacheClient,
    client_for_action: aiohttp.ClientSession,
) -> str:
    input_data = CacheableModel(
        parameter="hello",
    )

    return await cache_client.get_with_set(
        input_data=input_data,
        async_action=make_action,
        extra=client_for_action,
    )


@pytest.mark.asyncio
async def test_create_client() -> None:
    load_dotenv()
    base_url = os.environ.get("REMOTE_CACHE_BASE_URL", "https://some.domain:123")
    api_key = os.environ.get("REMOTE_CACHE_API_KEY", "api_key")

    remote_cache_client = await RemoteCacheClient.create(
        base_url=HttpUrl(base_url),
        api_key=api_key,
        namespace="debug",
        verify_ssl=False,
    )

    async with (
        remote_cache_client as cache_client,
        aiohttp.ClientSession() as client_for_action,
    ):
        result = await example(
            cache_client=cache_client,
            client_for_action=client_for_action,
        )

        assert result == "olleh"
