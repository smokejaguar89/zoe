import asyncio
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Responses that usually mean "try again shortly": rate limited, or the
# server (or a proxy in front of it) is temporarily overloaded or down
RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})


async def get_with_retries(
    url: str,
    params: Optional[dict[str, Any]] = None,
    *,
    timeout_seconds: float,
    max_attempts: int,
    retry_delay_seconds: float,
) -> httpx.Response:
    """GET a URL, retrying network errors and temporary HTTP errors.

    Waits retry_delay_seconds before the first retry and doubles the wait
    each time. Returns the last response, which may still be an error
    status for the caller to handle. Raises httpx.RequestError if the final
    attempt fails with a network error.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.get(url, params=params)
        except httpx.RequestError as error:
            if attempt == max_attempts:
                raise
            reason = str(error) or type(error).__name__
        else:
            if (
                response.status_code not in RETRYABLE_STATUS_CODES
                or attempt == max_attempts
            ):
                return response
            reason = f"HTTP {response.status_code}"

        delay = retry_delay_seconds * 2 ** (attempt - 1)
        # Log the URL only: params can contain API keys
        logger.warning(
            "GET %s failed (attempt %d/%d): %s; retrying in %.1fs",
            url,
            attempt,
            max_attempts,
            reason,
            delay,
        )
        await asyncio.sleep(delay)

    raise AssertionError("unreachable")
