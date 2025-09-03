import asyncio
import http
import logging
from logging import Logger
from types import TracebackType
from typing import Self

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .models import (
    CacheGetResult,
    CacheId,
    CacheRecordRequest,
    CacheRecordResponseOk,
    CacheRecordSetOutput,
    CacheStats,
    RetryConfig,
)
from .typing import T_INPUT_DATA_STR, T_NAMESPACE, T_OUTPUT_DATA_STR


class RemoteCacheClientBase(BaseModel):
    """Async client for interacting with a remote cache service."""

    namespace: str

    http_client: aiohttp.ClientSession
    verify_ssl: bool = True

    retry_config: RetryConfig = Field(default_factory=RetryConfig)

    cache_stats: CacheStats = Field(default_factory=CacheStats)

    logger: Logger = Field(default_factory=lambda: logging.getLogger(__name__))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @classmethod
    async def create(
        cls,
        base_url: HttpUrl,
        api_key: str,
        #
        namespace: T_NAMESPACE,
        *,
        verify_ssl: bool = True,
    ) -> Self:
        """Create a new instance with an initialized HTTP client."""
        client = aiohttp.ClientSession(
            base_url=str(base_url),
            headers={
                "X-API-Key": api_key,
            },
        )
        return cls(
            http_client=client,
            namespace=namespace,
            verify_ssl=verify_ssl,
        )

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
        await self.http_client.close()

    async def get(
        self,
        input_data: T_INPUT_DATA_STR,
        namespace_override: T_NAMESPACE | None = None,
    ) -> CacheGetResult:
        """Retrieve cached output for the given input data.

        Returns output string if found, otherwise CacheId.
        """
        namespace = namespace_override or self.namespace

        attempt = 1
        while True:
            async with self.http_client.post(
                "/api/v1/cache/text/get",
                json=CacheRecordRequest(
                    namespace=namespace,
                    input=input_data,
                ).model_dump(mode="json"),
                verify_ssl=self.verify_ssl,
            ) as response:
                if response.status == http.HTTPStatus.OK:
                    self.cache_stats.hits += 1
                    return CacheGetResult(
                        output=CacheRecordResponseOk.model_validate(
                            await response.json(),
                        ).output,
                    )
                if response.status == http.HTTPStatus.NOT_FOUND:
                    self.cache_stats.misses += 1
                    return CacheGetResult(
                        cache_id=CacheId.model_validate(await response.json()),
                    )

                msg = f"Unexpected response status: {response.status}. Details: {await response.text()}"

                # If this is the last attempt, raise an exception.
                # Else, wait with jitter

                if attempt >= self.retry_config.max_retries:
                    # sourcery skip: raise-specific-error
                    raise Exception(msg)  # noqa: TRY002

                wait_time = self.retry_config.get_wait_time(attempt)
                self.logger.warning(msg)
                self.logger.warning(f"Attempt {attempt} failed. Retrying in {wait_time} ms.")

                await asyncio.sleep(wait_time / 1000)
                attempt += 1

    async def set(self, cache_id: CacheId, output_data: T_OUTPUT_DATA_STR) -> None:
        """Store output data in the cache for the given cache_id."""
        attempt = 1
        while True:
            async with self.http_client.post(
                "/api/v1/cache/text/create",
                json=CacheRecordSetOutput(
                    cache_id=cache_id,
                    output=output_data,
                ).model_dump(mode="json"),
                verify_ssl=self.verify_ssl,
            ) as response:
                if response.status == http.HTTPStatus.OK:
                    return

                msg = f"Unexpected response status: {response.status}. Details: {await response.text()}"

                if attempt >= self.retry_config.max_retries:
                    # sourcery skip: raise-specific-error
                    raise Exception(msg)  # noqa: TRY002

                wait_time = self.retry_config.get_wait_time(attempt)
                self.logger.warning(msg)
                self.logger.warning(f"Attempt {attempt} failed. Retrying in {wait_time} ms.")

                await asyncio.sleep(wait_time / 1000)
                attempt += 1
