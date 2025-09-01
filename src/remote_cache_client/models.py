import random

from pydantic import BaseModel


class CacheId(BaseModel):
    namespace: str

    hash_name: str
    hash_value: str
    hash_length: int


class CacheRecordResponseOk(BaseModel):
    output: str


class CacheRecordRequest(BaseModel):
    namespace: str
    input: str


class CacheRecordSetOutput(BaseModel):
    cache_id: CacheId
    output: str


class CacheStats(BaseModel):
    hits: int = 0
    misses: int = 0


class CacheGetResult(BaseModel):
    output: str | None = None
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
