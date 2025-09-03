import logging
from collections.abc import Awaitable, Callable
from logging import Logger
from types import TracebackType
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .remote_cache_client_base import RemoteCacheClientBase
from .typing import T_NAMESPACE, T_OUTPUT_DATA_STR


class RemoteCacheClient(BaseModel):
    """Smart client for interacting with a remote cache service.

    Allows for:
    "transparent mode" (no cache used).
        When no config is provided, this client will not use a cache.
        Useful when cache is optional.

    pydantic-based simplified action.

    All this allows you to avoid boilerplate code in the application.
    """

    remote_cache_client: RemoteCacheClientBase | None = None

    logger: Logger = Field(default_factory=lambda: logging.getLogger(__name__))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @classmethod
    async def create(
        cls,
        base_url: None | HttpUrl,
        api_key: None | str,
        #
        namespace: T_NAMESPACE,
        *,
        verify_ssl: bool = True,
    ) -> Self:
        """Create a new RemoteCacheClientSmart instance with an initialized RemoteCacheClient if config is provided."""
        if base_url is not None and api_key is not None:
            remote_cache_client = await RemoteCacheClientBase.create(
                base_url=base_url,
                api_key=api_key,
                namespace=namespace,
                verify_ssl=verify_ssl,
            )
            return cls(remote_cache_client=remote_cache_client)
        logger = logging.getLogger(__name__)
        logger.warning("No config provided. Using transparent mode.")
        return cls(remote_cache_client=None)

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close HTTP client."""
        if self.remote_cache_client is not None:
            await self.remote_cache_client.http_client.close()



    async def get_with_set[Main: BaseModel, Extra](
        self,
        input_data: Main,
        async_action: Callable[[Main, Extra], Awaitable[T_OUTPUT_DATA_STR]],
        extra: Extra,
    ) -> T_OUTPUT_DATA_STR:
        if self.remote_cache_client is None:
            return await async_action(
                input_data,
                extra,
            )

        input_data_as_str = input_data.model_dump_json()

        result = await self.remote_cache_client.get(input_data_as_str)
        if result.is_hit():
            return result.get_output()

        data = await async_action(
            input_data,
            extra,
        )

        await self.remote_cache_client.set(
            cache_id=result.get_cache_id(),
            output_data=data,
        )

        return data
