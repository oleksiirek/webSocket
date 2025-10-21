"""Handlers package."""

from .error_handler import (
    ConnectionLimitError,
    DuplicateConnectionError,
    ErrorHandler,
    ErrorMiddleware,
    ShutdownInProgressError,
    WebSocketError,
)
from .multi_worker_shutdown import MultiWorkerShutdownCoordinator
from .shutdown_handler import ShutdownHandler

__all__ = [
    "ShutdownHandler",
    "MultiWorkerShutdownCoordinator",
    "ErrorHandler",
    "ErrorMiddleware",
    "WebSocketError",
    "ConnectionLimitError",
    "DuplicateConnectionError",
    "ShutdownInProgressError",
]
