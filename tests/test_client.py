import os

import pytest
from pydantic import HttpUrl

from remote_cache_client import RemoteCacheClient


@pytest.mark.asyncio
async def test_create_client() -> None:
    base_url = os.environ.get("REMOTE_CACHE_BASE_URL", "https://some.domain:123")
    api_key = os.environ.get("REMOTE_CACHE_API_KEY", "api_key")

    async with await RemoteCacheClient.create(
        base_url=HttpUrl(base_url),
        api_key=api_key,
        namespace="debug",
        verify_ssl=False,
    ):
        pass
