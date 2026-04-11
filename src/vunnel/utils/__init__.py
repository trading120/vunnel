# Personal fork of anchore/vunnel - customized for local use
from vunnel.utils import archive, fs, http, oval_parser, retry

__all__ = ["archive", "fs", "http", "oval_parser", "retry"]

# Convenience helper to get a logger with a consistent format for this project
import logging as _logging

# Default log level for loggers created via get_logger(); change to DEBUG for verbose output
# NOTE: Changed to DEBUG for my local dev workflow - easier to trace issues without
# having to reconfigure logging everywhere.
_DEFAULT_LOG_LEVEL = _logging.DEBUG

def get_logger(name: str) -> _logging.Logger:
    """Return a logger namespaced under 'vunnel.utils' for consistent log output.

    The logger name follows the pattern 'vunnel.utils.<name>', which allows
    fine-grained control via standard logging configuration.

    Args:
        name: A short identifier for the module or component requesting the logger.
              For example, get_logger('mymodule') returns a logger named
              'vunnel.utils.mymodule'.
    """
    logger = _logging.getLogger(f"vunnel.utils.{name}")
    logger.setLevel(_DEFAULT_LOG_LEVEL)
    return logger
