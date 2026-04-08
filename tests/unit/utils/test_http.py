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


def test_env_defaults(monkeypatch):
    monkeypatch.setenv("VUNNEL_HTTP_TIMEOUT", "60")
    monkeypatch.setenv("VUNNEL_HTTP_MAX_RETRIES", "5")
    monkeypatch.setenv("VUNNEL_HTTP_BACKOFF", "2.5")

    import importlib
    import vunnel.utils.http as http_module
    importlib.reload(http_module)

    assert http_module.DEFAULT_TIMEOUT == 60
    assert http_module.DEFAULT_MAX_RETRIES == 5
    assert http_module.DEFAULT_BACKOFF == 2.5
