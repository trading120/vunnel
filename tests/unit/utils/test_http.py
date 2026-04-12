from __future__ import annotations

import os
from unittest.mock import MagicMock, call, patch

import pytest
import requests

from vunnel.utils import http


@pytest.fixture()
def mock_response():
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"key": "value"}
    return resp


def test_get_returns_response(mock_response):
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = http.get("https://example.com/data", max_retries=1)
    mock_get.assert_called_once()
    assert result is mock_response


def test_get_json_returns_parsed_body(mock_response):
    with patch("requests.get", return_value=mock_response):
        result = http.get_json("https://example.com/data", max_retries=1)
    assert result == {"key": "value"}


def test_get_retries_on_500(mock_response):
    bad = MagicMock(spec=requests.Response)
    bad.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=500))

    with patch("requests.get", side_effect=[bad, mock_response]) as mock_get:
        with patch("time.sleep"):
            result = http.get("https://example.com/data", max_retries=2, backoff=0)
    assert mock_get.call_count == 2
    assert result is mock_response


def test_get_raises_after_max_retries():
    bad = MagicMock(spec=requests.Response)
    bad.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=503))

    with patch("requests.get", return_value=bad):
        with patch("time.sleep"):
            with pytest.raises(requests.HTTPError):
                http.get("https://example.com/data", max_retries=2, backoff=0)


def test_get_retries_on_429(mock_response):
    # 429 Too Many Requests should also be retried, not just 5xx errors
    bad = MagicMock(spec=requests.Response)
    bad.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=429))

    with patch("requests.get", side_effect=[bad, mock_response]) as mock_get:
        with patch("time.sleep"):
            result = http.get("https://example.com/data", max_retries=2, backoff=0)
    assert mock_get.call_count == 2
    assert result is mock_response


def test_get_retries_on_503(mock_response):
    # 503 Service Unavailable - verify it retries and eventually succeeds
    bad = MagicMock(spec=requests.Response)
    bad.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=503))

    with patch("requests.get", side_effect=[bad, bad, mock_response]) as mock_get:
        with patch("time.sleep"):
            result = http.get("https://example.com/data", max_retries=3, backoff=0)
    assert mock_get.call_count == 3
    assert result is mock_response


def test_get_raises_on_404():
    # 404 Not Found should NOT be retried - it's a client error, not transient.
    # Retrying 404s would just waste time and add unnecessary load to the server.
    bad = MagicMock(spec=requests.Response)
    bad.status_code = 404
    bad.raise_for_status.side_effect = requests.HTTPError(response=MagicMock(status_code=404))

    with patch("requests.get", return_value=bad) as mock_get:
        with patch("time.sleep"):
            with pytest.raises(requests.HTTPError):
                http.get("https://example.com/data", max_retries=3, backoff=0)
    # should only be called once - no retries for 404
    assert mock_get.call_count == 1
