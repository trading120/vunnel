# Personal fork of anchore/vunnel - customized for local use
from vunnel.utils import archive, fs, http, oval_parser, retry

__all__ = ["archive", "fs", "http", "oval_parser", "retry"]

# Convenience helper to get a logger with a consistent format for this project
import logging as _logging

def get_logger(name: str) -> _logging.Logger:
    """Return a logger namespaced under 'vunnel.utils' for consistent log output."""
    return _logging.getLogger(f"vunnel.utils.{name}")
