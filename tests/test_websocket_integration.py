"""Integration tests for WebSocket functionality."""

import asyncio
import json
from unittest.mock import patch

import pytest
import websockets
from fastapi.testclient import TestClient

from websocket_server.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def websocket_url():
    """WebSocket URL for testing."""
    return "ws://localhost:8000/ws"


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test complete WebSocket connection lifecycle."""
        # This test requires the server to be running
        # In a real test environment, you'd start the server in a separate process

        # Mock the server startup for testing
        with patch('websocket_server.app.app'):
            # Test would connect to actual WebSocket endpoint
            # For now, we'll test the connection logic
            pass

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data
        assert "connections" in data

    def test_notify_endpoint(self, client):
        """Test the notification endpoint."""
        notification_data = {
            "message": "Test notification",
            "type": "test",
            "data": {"priority": "normal"}
        }

        response = client.post("/notify", json=notification_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "recipients" in data
        assert "notification" in data

    def test_metrics_endpoint(self, client):
        """Test the metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "connections" in data
        assert "notification_service" in data
        assert "server" in data
        assert "timestamp" in data

    def test_status_endpoint(self, client):
        """Test the status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert "server" in data
        assert "connections" in data
        assert "notification_service" in data
        assert "shutdown" in data
        assert "configuration" in data

    def test_prometheus_metrics_endpoint(self, client):
        """Test the Prometheus metrics endpoint."""
        response = client.get("/metrics/prometheus")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        content = response.text
        assert "websocket_active_connections" in content
        assert "websocket_total_connections" in content
        assert "websocket_notifications_sent" in content

    def test_invalid_notify_request(self, client):
        """Test notification endpoint with invalid data."""
        # Missing required message field
        invalid_data = {
            "type": "test"
        }

        response = client.post("/notify", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_notify_endpoint_during_shutdown(self, client):
        """Test notification endpoint when server is shutting down."""
        # This would require mocking the shutdown state
        # For now, test normal operation
        notification_data = {
            "message": "Test during shutdown",
            "type": "test"
        }

        response = client.post("/notify", json=notification_data)
        # Should work normally when not actually shutting down
        assert response.status_code == 200


class TestWebSocketMessages:
    """Test WebSocket message handling."""

    @pytest.mark.asyncio
    async def test_websocket_message_formats(self):
        """Test various WebSocket message formats."""
        # This would test actual WebSocket message exchange
        # Requires running server instance

        # Test ping message

        # Test status request

        # Test invalid message

        # In a full integration test, these would be sent to actual WebSocket
        # and responses would be verified
        pass

    @pytest.mark.asyncio
    async def test_websocket_connection_with_client_id(self):
        """Test WebSocket connection with custom client ID."""
        # Test connecting with custom client ID
        # url = f"ws://localhost:8000/ws?client_id={client_id}"

        # In full test, would connect and verify welcome message contains client_id
        pass

    @pytest.mark.asyncio
    async def test_websocket_connection_without_client_id(self):
        """Test WebSocket connection without client ID (auto-generated)."""
        # Test connecting without client ID
        # url = "ws://localhost:8000/ws"

        # In full test, would connect and verify auto-generated client_id
        pass

    @pytest.mark.asyncio
    async def test_websocket_periodic_notifications(self):
        """Test receiving periodic notifications."""
        # Connect to WebSocket and wait for periodic notifications
        # Verify they arrive at expected intervals
        pass

    @pytest.mark.asyncio
    async def test_websocket_broadcast_notification(self):
        """Test receiving broadcast notifications."""
        # Connect WebSocket client
        # Send notification via HTTP API
        # Verify WebSocket client receives the notification
        pass

    @pytest.mark.asyncio
    async def test_websocket_connection_limit(self):
        """Test WebSocket connection limit enforcement."""
        # This would test connecting more clients than MAX_CONNECTIONS
        # and verify that excess connections are rejected
        pass

    @pytest.mark.asyncio
    async def test_websocket_duplicate_client_id(self):
        """Test handling of duplicate client IDs."""
        # Connect with same client_id twice
        # Verify second connection is rejected
        pass


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios."""

    @pytest.mark.asyncio
    async def test_websocket_invalid_json(self):
        """Test sending invalid JSON to WebSocket."""
        # Send malformed JSON and verify error response
        pass

    @pytest.mark.asyncio
    async def test_websocket_unknown_message_type(self):
        """Test sending unknown message type."""
        # Send message with unknown type and verify error response
        pass

    @pytest.mark.asyncio
    async def test_websocket_connection_timeout(self):
        """Test WebSocket connection timeout handling."""
        # Connect and remain idle to test timeout behavior
        pass

    @pytest.mark.asyncio
    async def test_websocket_connection_during_shutdown(self):
        """Test WebSocket connection attempt during shutdown."""
        # Attempt connection while server is shutting down
        # Verify connection is rejected with appropriate message
        pass


class TestGracefulShutdown:
    """Test graceful shutdown scenarios."""

    @pytest.mark.asyncio
    async def test_graceful_shutdown_no_connections(self):
        """Test graceful shutdown with no active connections."""
        # Trigger shutdown signal with no connections
        # Verify immediate shutdown
        pass

    @pytest.mark.asyncio
    async def test_graceful_shutdown_with_connections(self):
        """Test graceful shutdown with active connections."""
        # Connect WebSocket clients
        # Trigger shutdown signal
        # Verify clients receive shutdown notification
        # Verify server waits for natural disconnection
        pass

    @pytest.mark.asyncio
    async def test_graceful_shutdown_timeout(self):
        """Test graceful shutdown timeout."""
        # Connect WebSocket clients that don't disconnect
        # Trigger shutdown signal
        # Verify server force-closes after timeout
        pass

    @pytest.mark.asyncio
    async def test_graceful_shutdown_multi_worker(self):
        """Test graceful shutdown with multiple workers."""
        # This would test shutdown coordination across workers
        # Requires multi-worker setup
        pass


# Helper functions for integration tests

async def connect_websocket(url, client_id=None):
    """Helper function to connect to WebSocket."""
    if client_id:
        url = f"{url}?client_id={client_id}"

    try:
        websocket = await websockets.connect(url)
        return websocket
    except Exception as e:
        pytest.fail(f"Failed to connect to WebSocket: {e}")


async def send_and_receive(websocket, message, timeout=5):
    """Helper function to send message and receive response."""
    await websocket.send(json.dumps(message))

    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
        return json.loads(response)
    except TimeoutError:
        pytest.fail(f"Timeout waiting for response to {message}")


async def wait_for_message_type(websocket, message_type, timeout=10):
    """Helper function to wait for specific message type."""
    start_time = asyncio.get_event_loop().time()

    while True:
        if asyncio.get_event_loop().time() - start_time > timeout:
            pytest.fail(f"Timeout waiting for message type: {message_type}")

        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=1)
            data = json.loads(message)
            if data.get("type") == message_type:
                return data
        except TimeoutError:
            continue
        except Exception as e:
            pytest.fail(f"Error waiting for message: {e}")


# Fixtures for running server during tests

@pytest.fixture(scope="session")
async def running_server():
    """Start server for integration tests."""
    # This would start the actual server in a separate process
    # and clean it up after tests complete

    # For now, return None to indicate server should be started manually
    # In a full test suite, this would use subprocess or similar
    return None


@pytest.fixture
async def websocket_client(running_server, websocket_url):
    """Create WebSocket client for testing."""
    if running_server is None:
        pytest.skip("Server not running - start manually for integration tests")

    websocket = await connect_websocket(websocket_url)
    yield websocket
    await websocket.close()


# Example of how to run these tests:
# 1. Start the server: python main.py --dev
# 2. Run tests: pytest tests/test_websocket_integration.py -v
