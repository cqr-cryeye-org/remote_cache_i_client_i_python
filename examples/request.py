import aiohttp
from pydantic import BaseModel, HttpUrl

from remote_cache_client import RemoteCacheClient


class CacheableModel(BaseModel):
    parameter: str


async def make_action(
    data: CacheableModel,
    client_for_action: aiohttp.ClientSession,
) -> str:
    async with client_for_action.get("https://example.com") as resp:
        await resp.json()  # Just to show that we can use the client here
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


async def main() -> None:
    async with (
        await RemoteCacheClient.create(
            base_url=HttpUrl("https://some.domain:123"),
            api_key="api_key",
            namespace="debug",
            verify_ssl=False,
        ) as cache_client,
        aiohttp.ClientSession() as client_for_action,
    ):
        await example(
            cache_client=cache_client,
            client_for_action=client_for_action,
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
