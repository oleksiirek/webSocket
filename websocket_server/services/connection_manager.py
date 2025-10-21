"""WebSocket connection management service."""

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from ..config import settings
from ..models import ConnectionInfo


class ConnectionManager:
    """Manages WebSocket connections with thread-safe operations."""

    def __init__(self):
        """Initialize the connection manager."""
        self._connections: dict[str, WebSocket] = {}
        self._connection_info: dict[str, ConnectionInfo] = {}
        self._lock = asyncio.Lock()
        self._total_connections = 0

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection instance
            client_id: Unique identifier for the client

        Raises:
            ValueError: If client_id is already connected
        """
        async with self._lock:
            if client_id in self._connections:
                logger.warning(f"Client {client_id} attempted duplicate connection")
                raise ValueError(f"Client {client_id} is already connected")

            # Check connection limit
            if len(self._connections) >= settings.max_connections:
                logger.warning(
                    f"Connection limit reached ({settings.max_connections}), "
                    f"rejecting client {client_id}"
                )
                raise ValueError("Maximum connections exceeded")

            # Accept the connection
            await websocket.accept()

            # Store connection and metadata
            self._connections[client_id] = websocket
            self._connection_info[client_id] = ConnectionInfo(
                client_id=client_id,
                connected_at=datetime.now(UTC),
                user_agent=websocket.headers.get("user-agent")
            )
            self._total_connections += 1

            logger.info(
                f"Client {client_id} connected",
                extra={
                    "client_id": client_id,
                    "active_connections": len(self._connections),
                    "total_connections": self._total_connections
                }
            )

    async def disconnect(self, client_id: str) -> None:
        """
        Remove a client connection.

        Args:
            client_id: Unique identifier for the client to disconnect
        """
        async with self._lock:
            if client_id in self._connections:
                # Remove from tracking
                del self._connections[client_id]
                connection_info = self._connection_info.pop(client_id, None)

                # Calculate connection duration
                duration = None
                if connection_info:
                    duration = datetime.now(UTC) - connection_info.connected_at

                logger.info(
                    f"Client {client_id} disconnected",
                    extra={
                        "client_id": client_id,
                        "active_connections": len(self._connections),
                        "connection_duration": duration.total_seconds() if duration else None
                    }
                )
            else:
                logger.debug(f"Attempted to disconnect unknown client {client_id}")

    async def broadcast(self, message: dict) -> int:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Dictionary message to broadcast

        Returns:
            Number of clients that successfully received the message
        """
        if not self._connections:
            logger.debug("No active connections for broadcast")
            return 0

        successful_sends = 0
        failed_clients: set[str] = set()

        # Create a snapshot of connections to avoid lock contention
        async with self._lock:
            connections_snapshot = dict(self._connections)

        # Send messages without holding the lock
        for client_id, websocket in connections_snapshot.items():
            try:
                await websocket.send_json(message)
                successful_sends += 1

                # Update last ping time
                async with self._lock:
                    if client_id in self._connection_info:
                        self._connection_info[client_id].last_ping = datetime.now(UTC)

            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected during broadcast")
                failed_clients.add(client_id)
            except Exception as e:
                logger.error(
                    f"Failed to send message to client {client_id}: {e}",
                    extra={"client_id": client_id, "error": str(e)}
                )
                failed_clients.add(client_id)

        # Clean up failed connections
        if failed_clients:
            await self._cleanup_failed_connections(failed_clients)

        logger.debug(
            f"Broadcast completed: {successful_sends} successful, {len(failed_clients)} failed",
            extra={
                "successful_sends": successful_sends,
                "failed_sends": len(failed_clients),
                "message_type": message.get("type", "unknown")
            }
        )

        return successful_sends

    async def get_connection_count(self) -> int:
        """
        Get the current number of active connections.

        Returns:
            Number of active connections
        """
        async with self._lock:
            return len(self._connections)

    async def get_total_connections(self) -> int:
        """
        Get the total number of connections since server start.

        Returns:
            Total connection count
        """
        return self._total_connections

    async def get_connection_info(self, client_id: str) -> ConnectionInfo | None:
        """
        Get connection information for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            ConnectionInfo if client exists, None otherwise
        """
        async with self._lock:
            return self._connection_info.get(client_id)

    async def get_all_connection_info(self) -> dict[str, ConnectionInfo]:
        """
        Get connection information for all active clients.

        Returns:
            Dictionary mapping client IDs to ConnectionInfo
        """
        async with self._lock:
            return dict(self._connection_info)

    async def cleanup_stale_connections(self) -> int:
        """
        Remove connections that haven't sent a ping recently.

        Returns:
            Number of stale connections removed
        """
        if not self._connections:
            return 0

        stale_threshold = datetime.now(UTC) - timedelta(
            seconds=settings.ping_interval * 3  # 3x ping interval
        )
        stale_clients: set[str] = set()

        async with self._lock:
            for client_id, info in self._connection_info.items():
                # Check if connection is stale (no recent ping)
                last_activity = info.last_ping or info.connected_at
                if last_activity < stale_threshold:
                    stale_clients.add(client_id)

        # Remove stale connections
        if stale_clients:
            await self._cleanup_failed_connections(stale_clients)
            logger.info(
                f"Cleaned up {len(stale_clients)} stale connections",
                extra={"stale_count": len(stale_clients)}
            )

        return len(stale_clients)

    async def _cleanup_failed_connections(self, client_ids: set[str]) -> None:
        """
        Internal method to clean up failed or stale connections.

        Args:
            client_ids: Set of client IDs to remove
        """
        async with self._lock:
            for client_id in client_ids:
                if client_id in self._connections:
                    try:
                        # Try to close the WebSocket gracefully
                        websocket = self._connections[client_id]
                        await websocket.close()
                    except Exception as e:
                        logger.debug(f"Error closing WebSocket for {client_id}: {e}")

                    # Remove from tracking
                    del self._connections[client_id]
                    self._connection_info.pop(client_id, None)

    async def ping_all_connections(self) -> int:
        """
        Send ping to all active connections to check health.

        Returns:
            Number of successful pings
        """
        if not self._connections:
            return 0

        ping_message = {
            "type": "ping",
            "timestamp": datetime.now(UTC).isoformat()
        }

        return await self.broadcast(ping_message)

    async def shutdown_all_connections(self) -> None:
        """
        Gracefully close all active connections.
        """
        if not self._connections:
            logger.info("No active connections to shutdown")
            return

        # Send shutdown notification
        shutdown_message = {
            "type": "shutdown",
            "message": "Server is shutting down",
            "timestamp": datetime.now(UTC).isoformat()
        }

        await self.broadcast(shutdown_message)

        # Close all connections
        async with self._lock:
            client_ids = set(self._connections.keys())

        await self._cleanup_failed_connections(client_ids)

        logger.info(
            f"Shutdown complete: closed {len(client_ids)} connections",
            extra={"closed_connections": len(client_ids)}
        )
