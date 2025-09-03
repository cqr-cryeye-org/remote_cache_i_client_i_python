import random

from pydantic import BaseModel

from remote_cache_client.typing import T_INPUT_DATA_STR, T_NAMESPACE, T_OUTPUT_DATA_STR


class CacheId(BaseModel):
    namespace: T_NAMESPACE

    hash_name: str
    hash_value: str
    hash_length: int


class CacheRecordResponseOk(BaseModel):
    output: T_OUTPUT_DATA_STR


class CacheRecordRequest(BaseModel):
    namespace: T_NAMESPACE
    input: T_INPUT_DATA_STR


class CacheRecordSetOutput(BaseModel):
    cache_id: CacheId
    output: T_OUTPUT_DATA_STR


class CacheStats(BaseModel):
    hits: int = 0
    misses: int = 0


class CacheGetResult(BaseModel):
    output: T_OUTPUT_DATA_STR | None = None
    cache_id: CacheId | None = None

    def is_hit(self) -> bool:
        return self.output is not None

    def get_output(self) -> str:
        if self.output is None:
            msg = "Cache miss"
            # sourcery skip: raise-specific-error
            raise Exception(msg)  # noqa: TRY002

        return self.output

    def get_cache_id(self) -> CacheId:
        if self.cache_id is None:
            msg = "Cache miss"
            # sourcery skip: raise-specific-error
            raise Exception(msg)  # noqa: TRY002

        return self.cache_id


class RetryConfig(BaseModel):
    max_retries: int = 5
    jitter_percent: int = 40
    multiplier: int = 2

    base_wait_time_ms: int = 100  # in milliseconds

    def get_wait_time(self, attempt: int) -> int:
        # exponential-backoff-and-jitter
        # Jitter is random in the range [-jitter_value, jitter_value]

        base_value_for_attempt = self.base_wait_time_ms * (self.multiplier**attempt)

        jitter_value_side = base_value_for_attempt * (self.jitter_percent / 100)

        jitter_value = jitter_value_side * (2 * (random.random() - 0.5))  # noqa: S311

        return int(base_value_for_attempt + jitter_value)
