"""Unit tests for vunnel.utils.retry."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from vunnel.utils.retry import retry_request


class TransientError(Exception):
    """Simulated transient error."""


class PermanentError(Exception):
    """Simulated permanent error that should not be retried."""


def test_succeeds_on_first_attempt():
    mock_fn = MagicMock(return_value="ok")
    decorated = retry_request(retries=3)(mock_fn)

    result = decorated()

    assert result == "ok"
    assert mock_fn.call_count == 1


def test_retries_on_transient_error():
    mock_fn = MagicMock(side_effect=[TransientError("fail"), TransientError("fail"), "ok"])
    decorated = retry_request(retries=3, delay=0, on_exceptions=(TransientError,))(mock_fn)

    result = decorated()

    assert result == "ok"
    assert mock_fn.call_count == 3


def test_raises_after_max_retries():
    mock_fn = MagicMock(side_effect=TransientError("always fails"))
    decorated = retry_request(retries=2, delay=0, on_exceptions=(TransientError,))(mock_fn)

    with pytest.raises(TransientError, match="always fails"):
        decorated()

    assert mock_fn.call_count == 3  # initial + 2 retries


def test_does_not_retry_on_unexpected_exception():
    mock_fn = MagicMock(side_effect=PermanentError("permanent"))
    decorated = retry_request(retries=3, delay=0, on_exceptions=(TransientError,))(mock_fn)

    with pytest.raises(PermanentError):
        decorated()

    assert mock_fn.call_count == 1


def test_sleep_called_between_retries():
    """Verify that sleep is called with correct delay on first retry."""
    mock_fn = MagicMock(side_effect=[TransientError(), "ok"])
    decorated = retry_request(retries=2, delay=1.0, backoff=2.0, on_exceptions=(TransientError,))(mock_fn)

    with patch("vunnel.utils.retry.time.sleep") as mock_sleep:
        result = decorated()

    assert result == "ok"
    mock_sleep.assert_called_once_with(1.0)


def test_exponential_backoff():
    """Verify exponential backoff multiplies delay correctly across retries."""
    mock_fn = MagicMock(side_effect=[TransientError(), TransientError(), "ok"])
    decorated = retry_request(retries=3, delay=1.0, backoff=3.0, on_exceptions=(TransientError,))(mock_fn)

    with patch("vunnel.utils.retry.time.sleep") as mock_sleep:
        decorated()

    calls = [c.args[0] for c in mock_sleep.call_args_list]
    assert calls == [1.0, 3.0]
