"""Comprehensive error handling system for the WebSocket server."""

import traceback
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from loguru import logger

from ..config import settings


class ErrorCategories:
    """Error category constants."""
    CONNECTION = "connection"
    WEBSOCKET = "websocket"
    SYSTEM = "system"
    APPLICATION = "application"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"


class WebSocketError(Exception):
    """Base exception for WebSocket-related errors."""

    def __init__(self, message: str, code: int = 1011, client_id: str | None = None):
        """
        Initialize WebSocket error.

        Args:
            message: Error message
            code: WebSocket close code
            client_id: Optional client identifier
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.client_id = client_id
        self.error_id = str(uuid4())
        self.timestamp = datetime.now(UTC)


class ConnectionLimitError(WebSocketError):
    """Raised when connection limit is exceeded."""

    def __init__(self, current_count: int, max_count: int, client_id: str | None = None):
        message = f"Connection limit exceeded: {current_count}/{max_count}"
        super().__init__(message, code=1008, client_id=client_id)
        self.current_count = current_count
        self.max_count = max_count


class DuplicateConnectionError(WebSocketError):
    """Raised when client attempts duplicate connection."""

    def __init__(self, client_id: str):
        message = f"Client {client_id} is already connected"
        super().__init__(message, code=1008, client_id=client_id)


class ShutdownInProgressError(WebSocketError):
    """Raised when server is shutting down."""

    def __init__(self, client_id: str | None = None):
        message = "Server is shutting down"
        super().__init__(message, code=1001, client_id=client_id)


class ErrorHandler:
    """Centralized error handling with categorized error management."""

    @staticmethod
    async def handle_websocket_error(
        websocket: WebSocket,
        error: Exception,
        client_id: str | None = None
    ) -> None:
        """
        Handle WebSocket-specific errors with appropriate cleanup.

        Args:
            websocket: WebSocket connection instance
            error: Exception that occurred
            client_id: Optional client identifier
        """
        error_id = str(uuid4())

        # Determine error details
        if isinstance(error, WebSocketError):
            close_code = error.code
            error_message = error.message
            category = ErrorCategories.WEBSOCKET
        elif isinstance(error, WebSocketDisconnect):
            close_code = error.code
            error_message = f"Client disconnected: {error.reason or 'No reason provided'}"
            category = ErrorCategories.CONNECTION
        else:
            close_code = 1011  # Internal error
            error_message = "Internal server error"
            category = ErrorCategories.SYSTEM

        # Log the error
        logger.error(
            f"WebSocket error for client {client_id}: {error_message}",
            extra={
                "error_id": error_id,
                "client_id": client_id,
                "error_category": category,
                "error_type": type(error).__name__,
                "close_code": close_code,
                "error_message": str(error),
                "traceback": traceback.format_exc() if settings.debug else None
            }
        )

        # Try to send error message to client before closing
        try:
            if not isinstance(error, WebSocketDisconnect):
                await websocket.send_json({
                    "type": "error",
                    "error_id": error_id,
                    "message": error_message,
                    "code": close_code,
                    "timestamp": datetime.now(UTC).isoformat()
                })
        except Exception as send_error:
            logger.debug(f"Could not send error message to client {client_id}: {send_error}")

        # Close the connection
        try:
            await websocket.close(code=close_code, reason=error_message[:123])  # Max 123 bytes
        except Exception as close_error:
            logger.debug(f"Could not close WebSocket for client {client_id}: {close_error}")

    @staticmethod
    async def handle_broadcast_error(client_id: str, error: Exception) -> None:
        """
        Handle errors during message broadcasting.

        Args:
            client_id: Client identifier
            error: Exception that occurred during broadcast
        """
        error_id = str(uuid4())

        # Categorize the error
        if isinstance(error, WebSocketDisconnect):
            category = ErrorCategories.CONNECTION
            log_level = "info"
        elif isinstance(error, ConnectionError):
            category = ErrorCategories.CONNECTION
            log_level = "warning"
        else:
            category = ErrorCategories.APPLICATION
            log_level = "error"

        # Log with appropriate level
        log_message = f"Broadcast error for client {client_id}: {str(error)}"
        log_extra = {
            "error_id": error_id,
            "client_id": client_id,
            "error_category": category,
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc() if settings.debug else None
        }

        if log_level == "info":
            logger.info(log_message, extra=log_extra)
        elif log_level == "warning":
            logger.warning(log_message, extra=log_extra)
        else:
            logger.error(log_message, extra=log_extra)

    @staticmethod
    def handle_system_error(error: Exception, context: dict[str, Any] | None = None) -> str:
        """
        Handle system-level errors with proper logging.

        Args:
            error: Exception that occurred
            context: Optional context information

        Returns:
            Error ID for tracking
        """
        error_id = str(uuid4())

        # Determine error category
        if isinstance(error, (OSError, IOError)):
            category = ErrorCategories.SYSTEM
        elif isinstance(error, ValueError):
            category = ErrorCategories.VALIDATION
        else:
            category = ErrorCategories.APPLICATION

        # Log the error
        logger.error(
            f"System error: {str(error)}",
            extra={
                "error_id": error_id,
                "error_category": category,
                "error_type": type(error).__name__,
                "context": context or {},
                "traceback": traceback.format_exc()
            }
        )

        return error_id

    @staticmethod
    async def handle_http_error(request: Request, error: Exception) -> JSONResponse:
        """
        Handle HTTP endpoint errors.

        Args:
            request: FastAPI request object
            error: Exception that occurred

        Returns:
            JSON error response
        """
        error_id = str(uuid4())

        # Handle known error types
        if isinstance(error, HTTPException):
            status_code = error.status_code
            error_message = error.detail
            category = ErrorCategories.APPLICATION
        elif isinstance(error, ValueError):
            status_code = 400
            error_message = "Invalid request data"
            category = ErrorCategories.VALIDATION
        else:
            status_code = 500
            error_message = "Internal server error"
            category = ErrorCategories.SYSTEM

        # Log the error
        logger.error(
            f"HTTP error on {request.method} {request.url}: {str(error)}",
            extra={
                "error_id": error_id,
                "error_category": category,
                "error_type": type(error).__name__,
                "method": request.method,
                "url": str(request.url),
                "status_code": status_code,
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "traceback": traceback.format_exc() if settings.debug else None
            }
        )

        # Create error response
        error_response = {
            "error": {
                "id": error_id,
                "message": error_message,
                "category": category,
                "timestamp": datetime.now(UTC).isoformat()
            }
        }

        # Add debug information if in debug mode
        if settings.debug:
            error_response["error"]["debug"] = {
                "type": type(error).__name__,
                "traceback": traceback.format_exc()
            }

        return JSONResponse(
            status_code=status_code,
            content=error_response
        )

    @staticmethod
    def create_error_context(
        operation: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Create standardized error context for logging.

        Args:
            operation: Operation being performed when error occurred
            **kwargs: Additional context data

        Returns:
            Dictionary with error context
        """
        context = {
            "operation": operation,
            "timestamp": datetime.now(UTC).isoformat(),
            "server_info": {
                "debug_mode": settings.debug,
                "log_level": settings.log_level
            }
        }

        # Add any additional context
        context.update(kwargs)

        return context


class ErrorMiddleware:
    """Middleware for global error handling."""

    def __init__(self, app):
        """Initialize error middleware."""
        self.app = app

    async def __call__(self, scope, receive, send):
        """Handle requests with error catching."""
        if scope["type"] == "http":
            try:
                await self.app(scope, receive, send)
            except Exception as error:
                # Create a mock request for error handling
                request = Request(scope, receive)
                response = await ErrorHandler.handle_http_error(request, error)

                # Send the error response
                await response(scope, receive, send)
        else:
            # For WebSocket connections, let the endpoint handle errors
            await self.app(scope, receive, send)


# Utility functions for common error scenarios
async def handle_connection_error(
    websocket: WebSocket,
    client_id: str,
    current_connections: int,
    max_connections: int
) -> None:
    """Handle connection limit exceeded error."""
    error = ConnectionLimitError(current_connections, max_connections, client_id)
    await ErrorHandler.handle_websocket_error(websocket, error, client_id)


async def handle_duplicate_connection_error(
    websocket: WebSocket,
    client_id: str
) -> None:
    """Handle duplicate connection error."""
    error = DuplicateConnectionError(client_id)
    await ErrorHandler.handle_websocket_error(websocket, error, client_id)


async def handle_shutdown_error(
    websocket: WebSocket,
    client_id: str | None = None
) -> None:
    """Handle server shutdown error."""
    error = ShutdownInProgressError(client_id)
    await ErrorHandler.handle_websocket_error(websocket, error, client_id)
