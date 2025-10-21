"""Unit tests for ConnectionManager."""

from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from websocket_server.services.connection_manager import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create a ConnectionManager instance for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = AsyncMock(spec=WebSocket)
    websocket.headers = {"user-agent": "test-client"}
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


class TestConnectionManager:
    """Test cases for ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect_new_client(self, connection_manager, mock_websocket):
        """Test connecting a new client."""
        client_id = "test_client_1"

        await connection_manager.connect(mock_websocket, client_id)

        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()

        # Verify client is tracked
        assert await connection_manager.get_connection_count() == 1

        # Verify connection info is stored
        info = await connection_manager.get_connection_info(client_id)
        assert info is not None
        assert info.client_id == client_id
        assert info.user_agent == "test-client"

    @pytest.mark.asyncio
    async def test_connect_duplicate_client(self, connection_manager, mock_websocket):
        """Test connecting a client that's already connected."""
        client_id = "test_client_1"

        # Connect first time
        await connection_manager.connect(mock_websocket, client_id)

        # Try to connect again with same ID
        with pytest.raises(ValueError, match="already connected"):
            await connection_manager.connect(mock_websocket, client_id)

    @pytest.mark.asyncio
    async def test_disconnect_client(self, connection_manager, mock_websocket):
        """Test disconnecting a client."""
        client_id = "test_client_1"

        # Connect client
        await connection_manager.connect(mock_websocket, client_id)
        assert await connection_manager.get_connection_count() == 1

        # Disconnect client
        await connection_manager.disconnect(client_id)
        assert await connection_manager.get_connection_count() == 0

        # Verify connection info is removed
        info = await connection_manager.get_connection_info(client_id)
        assert info is None

    @pytest.mark.asyncio
    async def test_disconnect_unknown_client(self, connection_manager):
        """Test disconnecting a client that doesn't exist."""
        # Should not raise an error
        await connection_manager.disconnect("unknown_client")
        assert await connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self, connection_manager):
        """Test broadcasting a message to multiple clients."""
        # Create multiple mock WebSockets
        websockets = []
        client_ids = []

        for i in range(3):
            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"test-client-{i}"}
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            websockets.append(ws)

            client_id = f"test_client_{i}"
            client_ids.append(client_id)
            await connection_manager.connect(ws, client_id)

        # Broadcast message
        message = {"type": "test", "data": "hello"}
        recipients = await connection_manager.broadcast(message)

        # Verify all clients received the message
        assert recipients == 3
        for ws in websockets:
            ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_failed_client(self, connection_manager):
        """Test broadcasting when one client fails to receive."""
        # Create two mock WebSockets
        ws1 = AsyncMock(spec=WebSocket)
        ws1.headers = {"user-agent": "test-client-1"}
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock(spec=WebSocket)
        ws2.headers = {"user-agent": "test-client-2"}
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock(side_effect=Exception("Connection failed"))
        ws2.close = AsyncMock()

        # Connect both clients
        await connection_manager.connect(ws1, "client_1")
        await connection_manager.connect(ws2, "client_2")

        # Broadcast message
        message = {"type": "test", "data": "hello"}
        recipients = await connection_manager.broadcast(message)

        # Only one client should have received the message
        assert recipients == 1
        ws1.send_json.assert_called_once_with(message)

        # Failed client should be cleaned up
        assert await connection_manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_no_clients(self, connection_manager):
        """Test broadcasting when no clients are connected."""
        message = {"type": "test", "data": "hello"}
        recipients = await connection_manager.broadcast(message)

        assert recipients == 0

    @pytest.mark.asyncio
    async def test_get_all_connection_info(self, connection_manager, mock_websocket):
        """Test getting all connection information."""
        # Connect multiple clients
        client_ids = ["client_1", "client_2", "client_3"]
        for client_id in client_ids:
            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"test-{client_id}"}
            ws.accept = AsyncMock()
            await connection_manager.connect(ws, client_id)

        # Get all connection info
        all_info = await connection_manager.get_all_connection_info()

        assert len(all_info) == 3
        for client_id in client_ids:
            assert client_id in all_info
            assert all_info[client_id].client_id == client_id

    @pytest.mark.asyncio
    async def test_ping_all_connections(self, connection_manager):
        """Test pinging all connected clients."""
        # Connect multiple clients
        websockets = []
        for i in range(2):
            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"test-client-{i}"}
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            websockets.append(ws)
            await connection_manager.connect(ws, f"client_{i}")

        # Ping all connections
        recipients = await connection_manager.ping_all_connections()

        assert recipients == 2
        for ws in websockets:
            ws.send_json.assert_called_once()
            # Verify ping message format
            call_args = ws.send_json.call_args[0][0]
            assert call_args["type"] == "ping"
            assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_shutdown_all_connections(self, connection_manager):
        """Test shutting down all connections."""
        # Connect multiple clients
        websockets = []
        for i in range(2):
            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"test-client-{i}"}
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            ws.close = AsyncMock()
            websockets.append(ws)
            await connection_manager.connect(ws, f"client_{i}")

        # Shutdown all connections
        await connection_manager.shutdown_all_connections()

        # Verify shutdown message was sent to all clients
        for ws in websockets:
            ws.send_json.assert_called()
            call_args = ws.send_json.call_args[0][0]
            assert call_args["type"] == "shutdown"

        # Verify all connections were closed
        assert await connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections(self, connection_manager):
        """Test cleanup of stale connections."""
        # This test would require mocking datetime to simulate stale connections
        # For now, test that it doesn't crash with no stale connections
        stale_count = await connection_manager.cleanup_stale_connections()
        assert stale_count == 0

    @pytest.mark.asyncio
    async def test_get_total_connections(self, connection_manager, mock_websocket):
        """Test getting total connection count."""
        initial_total = await connection_manager.get_total_connections()

        # Connect and disconnect a client
        await connection_manager.connect(mock_websocket, "test_client")
        await connection_manager.disconnect("test_client")

        # Total should have increased
        final_total = await connection_manager.get_total_connections()
        assert final_total == initial_total + 1
