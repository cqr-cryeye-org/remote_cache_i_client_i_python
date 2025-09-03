# Remote cache. Client

Library for the client to remote cache.

Useful for sharing an already calculated result of the processing between different processors/applications.

---

## Dev

### Register pre-commit hooks

```shell
pre-commit install
```

### Run pre-commit hooks

```shell
pre-commit run --all-files
```

---

## Example:

```python
from pydantic import HttpUrl
from remote_cache_client import RemoteCacheClientBase


async def make_action() -> str:
    return "world"


async def example(cache_client: RemoteCacheClientBase) -> str:
    input_data = "hello"

    cache_result = await cache_client.get(input_data)

    print(cache_result)

    if cache_result.is_hit():
        print("Cache hit")
        return cache_result.get_output()

    print("Cache miss")
    action_result = await make_action()

    await cache_client.set(
        cache_id=cache_result.get_cache_id(),
        output_data=action_result,
    )
    return action_result


async def main() -> None:
    async with await RemoteCacheClientBase.create(
            base_url=HttpUrl("https://some.domain:123"),
            api_key="api_key",
            namespace="debug",
            verify_ssl=False,
    ) as cache_client:
        await example(cache_client)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

```