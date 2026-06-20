from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager

import structlog

log = structlog.get_logger()


@contextmanager
def timed_operation(name: str, **extra: object) -> Generator[None, None, None]:
    """Context manager that logs operation name and elapsed milliseconds."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info("operation_completed", operation=name, latency_ms=elapsed_ms, **extra)
