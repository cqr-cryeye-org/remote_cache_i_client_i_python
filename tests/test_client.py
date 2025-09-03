import pytest
from pydantic import BaseModel, HttpUrl

from remote_cache_client import RemoteCacheClient


class CacheableModel(BaseModel):
    parameter: str


async def make_action(data: CacheableModel) -> str:
    return data.parameter[::-1]  # Just an example action


async def example(cache_client: RemoteCacheClient) -> str:
    input_data = CacheableModel(
        parameter="hello",
    )

    return await cache_client.get_with_set(
        input_data=input_data,
        async_action=make_action,
    )


async def main() -> None:
    async with await RemoteCacheClient.create(
        base_url=HttpUrl("https://some.domain:123"),
        api_key="api_key",
        namespace="debug",
        verify_ssl=False,
    ) as cache_client:
        await example(cache_client)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


@pytest.mark.asyncio
async def test_create_client() -> None:
    async with await RemoteCacheClient.create(
        base_url=HttpUrl("https://some.domain:123"),
        api_key="api_key",
        namespace="debug",
        verify_ssl=False,
    ):
        pass
