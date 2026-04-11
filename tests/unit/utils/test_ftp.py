"""Tests for vunnel.utils.ftp module."""

from __future__ import annotations

import ftplib
from io import BytesIO
from unittest.mock import MagicMock, call, patch

import pytest

from vunnel.utils.ftp import download, list_directory


FTP_HOST = "ftp.example.com"
FTP_PATH = "/pub/data/file.tar.gz"
FTP_DIR = "/pub/data"


@pytest.fixture()
def mock_ftp(tmp_path):
    """Return a mock FTP connection and a helper to configure it."""
    ftp = MagicMock(spec=ftplib.FTP)
    ftp.__enter__ = MagicMock(return_value=ftp)
    ftp.__exit__ = MagicMock(return_value=False)
    return ftp


class TestDownload:
    def test_download_creates_destination_file(self, tmp_path, mock_ftp):
        """download() should write the remote file to the given local path."""
        dest = tmp_path / "file.tar.gz"
        payload = b"binary content"

        def fake_retrbinary(cmd, callback, **kwargs):
            callback(payload)

        mock_ftp.retrbinary.side_effect = fake_retrbinary

        with patch("ftplib.FTP", return_value=mock_ftp):
            result = download(FTP_HOST, FTP_PATH, str(dest))

        assert dest.exists()
        assert dest.read_bytes() == payload
        assert result == str(dest)

    def test_download_connects_to_correct_host(self, tmp_path, mock_ftp):
        """download() should connect to the specified FTP host."""
        dest = tmp_path / "file.tar.gz"
        mock_ftp.retrbinary.side_effect = lambda cmd, cb, **kw: cb(b"")

        with patch("ftplib.FTP", return_value=mock_ftp) as ftp_cls:
            download(FTP_HOST, FTP_PATH, str(dest))

        ftp_cls.assert_called_once_with(FTP_HOST)

    def test_download_logs_in_anonymously(self, tmp_path, mock_ftp):
        """download() should perform an anonymous login when no credentials given."""
        dest = tmp_path / "file.tar.gz"
        mock_ftp.retrbinary.side_effect = lambda cmd, cb, **kw: cb(b"")

        with patch("ftplib.FTP", return_value=mock_ftp):
            download(FTP_HOST, FTP_PATH, str(dest))

        mock_ftp.login.assert_called_once()

    def test_download_uses_correct_retr_command(self, tmp_path, mock_ftp):
        """download() should issue RETR with the remote path."""
        dest = tmp_path / "file.tar.gz"
        mock_ftp.retrbinary.side_effect = lambda cmd, cb, **kw: cb(b"")

        with patch("ftplib.FTP", return_value=mock_ftp):
            download(FTP_HOST, FTP_PATH, str(dest))

        call_args = mock_ftp.retrbinary.call_args
        assert f"RETR {FTP_PATH}" in call_args[0][0]

    def test_download_raises_on_ftp_error(self, tmp_path, mock_ftp):
        """download() should propagate FTP errors to the caller."""
        dest = tmp_path / "file.tar.gz"
        mock_ftp.retrbinary.side_effect = ftplib.error_perm("550 No such file")

        with patch("ftplib.FTP", return_value=mock_ftp):
            with pytest.raises(ftplib.error_perm):
                download(FTP_HOST, FTP_PATH, str(dest))

    def test_download_destination_file_not_created_on_error(self, tmp_path, mock_ftp):
        """download() should not leave a partial file behind when an FTP error occurs."""
        # NOTE: I noticed there was no test verifying cleanup on failure - adding one.
        dest = tmp_path / "file.tar.gz"
        mock_ftp.retrbinary.side_effect = ftplib.error_perm("550 No such file")

        with patch("ftplib.FTP", return_value=mock_ftp):
            with pytest.raises(ftplib.error_perm):
                download(FTP_HOST, FTP_PATH, str(dest))

        assert not dest.exists(), "Partial destination file should be cleaned up on error"


class TestListDirectory:
    def test_list_directory
