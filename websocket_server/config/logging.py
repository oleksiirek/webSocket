"""Loguru structured logging configuration."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from .settings import settings


class LoguruConfig:
    """Loguru logging configuration manager."""

    def __init__(self):
        """Initialize logging configuration."""
        self.is_configured = False
        self.log_dir = Path("logs")

    def configure_logging(self) -> None:
        """Configure Loguru logging with structured output."""
        if self.is_configured:
            return

        # Remove default handler
        logger.remove()

        # Create logs directory
        self.log_dir.mkdir(exist_ok=True)

        # Configure console handler
        self._configure_console_handler()

        # Configure file handler
        self._configure_file_handler()

        # Configure error file handler
        self._configure_error_file_handler()

        # Set up exception catching
        self._configure_exception_catching()

        self.is_configured = True

        logger.info(
            "Loguru logging configured",
            extra={
                "log_level": settings.log_level,
                "log_format": settings.log_format,
                "log_rotation": settings.log_rotation,
                "log_retention": settings.log_retention
            }
        )

    def _configure_console_handler(self) -> None:
        """Configure console output handler."""
        if settings.log_format == "json":
            # JSON format for production - structured but readable
            console_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
            console_serialize = False  # Don't serialize to console for readability
        else:
            # Human-readable format for development
            console_format = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
            console_serialize = False

        logger.add(
            sys.stdout,
            format=console_format,
            level=settings.log_level,
            serialize=console_serialize,
            backtrace=settings.debug,
            diagnose=settings.debug,
            colorize=not console_serialize,
            filter=self._console_filter
        )

    def _configure_file_handler(self) -> None:
        """Configure main log file handler."""
        log_file = self.log_dir / "websocket_server.log"

        logger.add(
            log_file,
            level=settings.log_level,
            serialize=True,  # Automatic JSON serialization
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="gz",
            backtrace=settings.debug,
            diagnose=settings.debug,
            enqueue=True  # Thread-safe logging
        )

    def _configure_error_file_handler(self) -> None:
        """Configure error-only log file handler."""
        error_log_file = self.log_dir / "errors.log"

        logger.add(
            error_log_file,
            level="ERROR",
            serialize=True,  # Automatic JSON serialization
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="gz",
            backtrace=True,
            diagnose=True,
            enqueue=True,
            filter=lambda record: record["level"].no >= logger.level("ERROR").no
        )

    def _configure_exception_catching(self) -> None:
        """Configure automatic exception catching."""
        if settings.debug:
            # In debug mode, catch all exceptions
            logger.add(
                sys.stderr,
                level="ERROR",
                serialize=True,  # Automatic JSON serialization
                backtrace=True,
                diagnose=True,
                catch=True
            )

    def _get_text_format(self) -> str:
        """Get text format string for structured logging."""
        return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"

    def _console_filter(self, record: dict[str, Any]) -> bool:
        """
        Filter console output based on environment.

        Args:
            record: Log record

        Returns:
            True if record should be logged to console
        """
        # In production, reduce console noise
        if not settings.debug:
            # Only show INFO and above for non-debug modules
            if record["level"].no < logger.level("INFO").no:
                return False

            # Filter out some noisy modules in production
            noisy_modules = ["uvicorn.access", "asyncio"]
            if any(module in record["name"] for module in noisy_modules):
                return record["level"].no >= logger.level("WARNING").no

        return True


class ContextualLogger:
    """Contextual logger with automatic binding."""

    def __init__(self):
        """Initialize contextual logger."""
        self._context: dict[str, Any] = {}

    def bind_context(self, **kwargs) -> None:
        """
        Bind context data to all subsequent log messages.

        Args:
            **kwargs: Context data to bind
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all bound context."""
        self._context.clear()

    def get_logger(self, **extra_context) -> Any:
        """
        Get logger with bound context.

        Args:
            **extra_context: Additional context for this log message

        Returns:
            Logger with bound context
        """
        combined_context = {**self._context, **extra_context}
        return logger.bind(**combined_context)

    def info(self, message: str, **extra_context) -> None:
        """Log info message with context."""
        self.get_logger(**extra_context).info(message)

    def debug(self, message: str, **extra_context) -> None:
        """Log debug message with context."""
        self.get_logger(**extra_context).debug(message)

    def warning(self, message: str, **extra_context) -> None:
        """Log warning message with context."""
        self.get_logger(**extra_context).warning(message)

    def error(self, message: str, **extra_context) -> None:
        """Log error message with context."""
        self.get_logger(**extra_context).error(message)

    def critical(self, message: str, **extra_context) -> None:
        """Log critical message with context."""
        self.get_logger(**extra_context).critical(message)


class RequestLogger:
    """Logger for HTTP requests with correlation IDs."""

    @staticmethod
    def log_request(
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        client_ip: str | None = None,
        user_agent: str | None = None,
        correlation_id: str | None = None
    ) -> None:
        """
        Log HTTP request with structured data.

        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            client_ip: Client IP address
            user_agent: User agent string
            correlation_id: Request correlation ID
        """
        logger.info(
            f"{method} {url} - {status_code}",
            extra={
                "request": {
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "correlation_id": correlation_id
                }
            }
        )


class WebSocketLogger:
    """Logger for WebSocket events with client tracking."""

    @staticmethod
    def log_connection(
        client_id: str,
        event: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
        **extra_data
    ) -> None:
        """
        Log WebSocket connection event.

        Args:
            client_id: Client identifier
            event: Event type (connect, disconnect, error, etc.)
            client_ip: Client IP address
            user_agent: User agent string
            **extra_data: Additional event data
        """
        logger.info(
            f"WebSocket {event}: {client_id}",
            extra={
                "websocket": {
                    "client_id": client_id,
                    "event": event,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    **extra_data
                }
            }
        )

    @staticmethod
    def log_message(
        client_id: str,
        direction: str,  # "sent" or "received"
        message_type: str,
        message_size: int,
        **extra_data
    ) -> None:
        """
        Log WebSocket message.

        Args:
            client_id: Client identifier
            direction: Message direction
            message_type: Type of message
            message_size: Message size in bytes
            **extra_data: Additional message data
        """
        logger.debug(
            f"WebSocket message {direction}: {client_id}",
            extra={
                "websocket_message": {
                    "client_id": client_id,
                    "direction": direction,
                    "message_type": message_type,
                    "message_size": message_size,
                    **extra_data
                }
            }
        )


# Global instances
loguru_config = LoguruConfig()
contextual_logger = ContextualLogger()


def setup_logging() -> None:
    """Set up application logging."""
    loguru_config.configure_logging()


def get_contextual_logger() -> ContextualLogger:
    """
    Get contextual logger instance.

    Returns:
        ContextualLogger instance
    """
    return contextual_logger


# Convenience functions
def log_startup_info() -> None:
    """Log application startup information."""
    logger.info(
        "WebSocket Notification Server starting up",
        extra={
            "startup": {
                "timestamp": datetime.now(UTC).isoformat(),
                "settings": {
                    "host": settings.host,
                    "port": settings.port,
                    "workers": settings.workers,
                    "debug": settings.debug,
                    "log_level": settings.log_level,
                    "max_connections": settings.max_connections
                }
            }
        }
    )


def log_shutdown_info() -> None:
    """Log application shutdown information."""
    logger.info(
        "WebSocket Notification Server shutting down",
        extra={
            "shutdown": {
                "timestamp": datetime.now(UTC).isoformat()
            }
        }
    )
