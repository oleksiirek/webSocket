"""WebSocket endpoint implementation."""

import asyncio
import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from ..dependencies import get_connection_manager, get_shutdown_handler
from ..handlers import ShutdownHandler
from ..services import ConnectionManager


async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str | None = None,
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    shutdown_handler: ShutdownHandler = Depends(get_shutdown_handler)
):
    """
    WebSocket endpoint for client connections.

    Args:
        websocket: WebSocket connection instance
        client_id: Optional client identifier (generated if not provided)
        connection_manager: ConnectionManager dependency
        shutdown_handler: ShutdownHandler dependency
    """
    # Generate client ID if not provided
    if not client_id:
        client_id = f"client_{uuid4().hex[:8]}"

    logger.info(
        f"WebSocket connection attempt from client {client_id}",
        extra={
            "client_id": client_id,
            "client_host": websocket.client.host if websocket.client else "unknown",
            "user_agent": websocket.headers.get("user-agent", "unknown")
        }
    )

    # Check if shutdown is in progress
    if shutdown_handler.is_shutdown_requested():
        logger.warning(
            f"Rejecting connection from {client_id} - server shutting down",
            extra={"client_id": client_id}
        )
        await websocket.close(code=1001, reason="Server shutting down")
        return

    try:
        # Connect the client
        await connection_manager.connect(websocket, client_id)

        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "message": "Connected to WebSocket Notification Server",
            "client_id": client_id,
            "server_time": datetime.now(UTC).isoformat(),
            "notification_interval": 10  # From settings
        }
        await websocket.send_json(welcome_message)

        # Handle incoming messages
        await handle_websocket_messages(websocket, client_id, connection_manager, shutdown_handler)

    except ValueError as e:
        # Connection rejected (duplicate client_id or max connections)
        logger.warning(
            f"Connection rejected for client {client_id}: {e}",
            extra={"client_id": client_id, "error": str(e)}
        )
        await websocket.close(code=1008, reason=str(e))

    except WebSocketDisconnect:
        logger.info(
            f"Client {client_id} disconnected normally",
            extra={"client_id": client_id}
        )

    except Exception as e:
        logger.error(
            f"Unexpected error for client {client_id}: {e}",
            extra={"client_id": client_id, "error": str(e)}
        )
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass  # Connection might already be closed

    finally:
        # Ensure client is disconnected from manager
        await connection_manager.disconnect(client_id)


async def handle_websocket_messages(
    websocket: WebSocket,
    client_id: str,
    connection_manager: ConnectionManager,
    shutdown_handler: ShutdownHandler
):
    """
    Handle incoming WebSocket messages from a client.

    Args:
        websocket: WebSocket connection instance
        client_id: Client identifier
        connection_manager: ConnectionManager instance
        shutdown_handler: ShutdownHandler instance
    """
    try:
        while True:
            # Check if shutdown is requested
            if shutdown_handler.is_shutdown_requested():
                logger.info(
                    f"Closing connection for {client_id} due to shutdown",
                    extra={"client_id": client_id}
                )
                break

            # Wait for message with timeout
            try:
                # Use asyncio.wait_for to add timeout
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )
            except TimeoutError:
                # Send ping to check if connection is alive
                try:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.now(UTC).isoformat()
                    })
                    continue
                except Exception:
                    # Connection is dead
                    logger.info(
                        f"Client {client_id} connection timeout - no response to ping",
                        extra={"client_id": client_id}
                    )
                    break

            # Process the message
            await process_client_message(websocket, client_id, message, connection_manager)

    except WebSocketDisconnect:
        logger.info(
            f"Client {client_id} disconnected during message handling",
            extra={"client_id": client_id}
        )
    except Exception as e:
        logger.error(
            f"Error handling messages for client {client_id}: {e}",
            extra={"client_id": client_id, "error": str(e)}
        )


async def process_client_message(
    websocket: WebSocket,
    client_id: str,
    message: str,
    connection_manager: ConnectionManager
):
    """
    Process a message received from a client.

    Args:
        websocket: WebSocket connection instance
        client_id: Client identifier
        message: Raw message string from client
        connection_manager: ConnectionManager instance
    """
    try:
        # Parse JSON message
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await send_error_response(
                websocket,
                "Invalid JSON format",
                client_id
            )
            return

        message_type = data.get("type", "unknown")

        logger.debug(
            f"Received message from client {client_id}",
            extra={
                "client_id": client_id,
                "message_type": message_type,
                "message_size": len(message)
            }
        )

        # Handle different message types
        if message_type == "pong":
            # Update last ping time
            connection_info = await connection_manager.get_connection_info(client_id)
            if connection_info:
                connection_info.last_ping = datetime.now(UTC)

            logger.debug(
                f"Received pong from client {client_id}",
                extra={"client_id": client_id}
            )

        elif message_type == "ping":
            # Respond with pong
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now(UTC).isoformat()
            })

        elif message_type == "status_request":
            # Send connection status
            stats = await get_connection_stats(connection_manager)
            await websocket.send_json({
                "type": "status_response",
                "data": stats,
                "timestamp": datetime.now(UTC).isoformat()
            })

        else:
            # Unknown message type
            await send_error_response(
                websocket,
                f"Unknown message type: {message_type}",
                client_id
            )

    except Exception as e:
        logger.error(
            f"Error processing message from client {client_id}: {e}",
            extra={"client_id": client_id, "error": str(e), "message": message}
        )
        await send_error_response(websocket, "Internal server error", client_id)


async def send_error_response(websocket: WebSocket, error_message: str, client_id: str):
    """
    Send an error response to the client.

    Args:
        websocket: WebSocket connection instance
        error_message: Error message to send
        client_id: Client identifier for logging
    """
    try:
        await websocket.send_json({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now(UTC).isoformat()
        })
    except Exception as e:
        logger.error(
            f"Failed to send error response to client {client_id}: {e}",
            extra={"client_id": client_id, "error": str(e)}
        )


async def get_connection_stats(connection_manager: ConnectionManager) -> dict:
    """
    Get connection statistics for status responses.

    Args:
        connection_manager: ConnectionManager instance

    Returns:
        Dictionary with connection statistics
    """
    return {
        "active_connections": await connection_manager.get_connection_count(),
        "total_connections": await connection_manager.get_total_connections(),
        "server_time": datetime.now(UTC).isoformat()
    }
