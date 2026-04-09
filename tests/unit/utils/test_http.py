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


def test_download_file_writes_content(tmp_path):
    dest = str(tmp_path / "output.bin")
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [b"hello ", b"world"]

    with patch("requests.get", return_value=mock_resp):
        result = http.download_file("https://example.com/file.bin", dest, max_retries=1)

    assert result == dest
    assert open(dest, "rb").read() == b"hello world"


def test_download_file_returns_path_string(tmp_path):
    # Ensure the return value is always a str, not a Path object
    dest = tmp_path / "output.bin"
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [b"data"]

    with patch("requests.get", return_value=mock_resp):
        result = http.download_file("https://example.com/file.bin", dest, max_retries=1)

    assert isinstance(result, str)
