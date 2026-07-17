import asyncio
import functools
import logging
import random

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=10.0)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def with_retry(max_attempts: int = 4, base_delay: float = 1.0, max_delay: float = 30.0):
    """Retries on 403/429 and transport errors with exponential backoff + jitter."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    response = await func(*args, **kwargs)
                    if isinstance(response, httpx.Response) and response.status_code in (403, 429):
                        raise httpx.HTTPStatusError(
                            f"status {response.status_code}", request=response.request, response=response
                        )
                    return response
                except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                    last_exc = exc
                    if attempt == max_attempts - 1:
                        break
                    jitter = random.uniform(0, delay * 0.1)
                    logger.warning("Request failed (attempt %d/%d), retrying in %.1fs: %s",
                                   attempt + 1, max_attempts, delay + jitter, exc)
                    await asyncio.sleep(delay + jitter)
                    delay = min(delay * 2, max_delay)
            raise last_exc

        return wrapper

    return decorator
