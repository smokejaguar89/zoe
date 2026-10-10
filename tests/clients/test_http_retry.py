import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

from app.clients.http_retry import get_with_retries


def _response(status_code: int) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    return response


def _get(responses, **kwargs):
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=responses)
    with (
        patch("app.clients.http_retry.httpx.AsyncClient") as MockAsyncClient,
        patch(
            "app.clients.http_retry.asyncio.sleep", new=AsyncMock()
        ) as sleep_mock,
    ):
        MockAsyncClient.return_value.__aenter__ = AsyncMock(
            return_value=mock_http_client
        )
        MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=None)
        response = asyncio.run(
            get_with_retries(
                "https://example.test/api",
                timeout_seconds=1.0,
                max_attempts=3,
                retry_delay_seconds=1.0,
                **kwargs,
            )
        )
    return response, mock_http_client.get, sleep_mock


def test_returns_first_successful_response_without_retrying() -> None:
    response, get, sleep = _get([_response(200)])

    assert response.status_code == 200
    assert get.call_count == 1
    sleep.assert_not_awaited()


def test_retries_each_temporary_status() -> None:
    for status_code in (429, 502, 503, 504):
        response, get, _ = _get([_response(status_code), _response(200)])

        assert response.status_code == 200, status_code
        assert get.call_count == 2, status_code


def test_does_not_retry_other_errors() -> None:
    response, get, sleep = _get([_response(404)])

    assert response.status_code == 404
    assert get.call_count == 1
    sleep.assert_not_awaited()


def test_returns_last_error_response_after_max_attempts() -> None:
    response, get, sleep = _get([_response(503)] * 3)

    assert response.status_code == 503
    assert get.call_count == 3
    assert [call.args[0] for call in sleep.await_args_list] == [1.0, 2.0]


def test_does_not_log_params(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="app.clients.http_retry"):
        _get(
            [_response(503), _response(200)],
            params={"apiKey": "secret-key"},
        )

    assert "HTTP 503" in caplog.text
    assert "secret-key" not in caplog.text
