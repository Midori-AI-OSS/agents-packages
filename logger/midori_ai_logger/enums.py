"""Log level enumeration for Midori AI logger."""

from enum import Enum


class LogLevel(str, Enum):
    """Standardized log level values for the Midori AI logger."""

    NORMAL = "normal"
    DEBUG = "debug"
    WARN = "warn"
    ERROR = "error"
