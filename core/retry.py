from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 8.0
    jitter: bool = True


def run_with_retry(
    operation: Callable[[], T],
    policy: RetryPolicy,
    should_retry: Callable[[Exception], bool] | None = None,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, policy.attempts + 1):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - behavior validated by callers
            last_error = exc
            if should_retry is not None and not should_retry(exc):
                raise
            if attempt >= policy.attempts:
                break
            base_delay = min(
                policy.max_delay_seconds,
                policy.base_delay_seconds * (2 ** (attempt - 1)),
            )
            delay = (
                base_delay * (0.5 + random.random() * 0.5)
                if policy.jitter
                else base_delay
            )
            time.sleep(delay)
    if last_error is None:
        raise RuntimeError("Retry operation did not execute.")
    raise last_error
