"""Load and performance tests for WebSocket Notification Server."""

import asyncio
import time
from unittest.mock import patch

import pytest

from websocket_server.app import app
from websocket_server.services.connection_manager import ConnectionManager
from websocket_server.services.notification_service import NotificationService


class TestPerformance:
    """Performance tests for core components."""

    @pytest.mark.asyncio
    async def test_connection_manager_performance(self):
        """Test ConnectionManager performance with many connections."""
        manager = ConnectionManager()

        # Create mock WebSockets
        mock_websockets = []
        client_ids = []

        start_time = time.time()

        # Test connecting many clients
        for i in range(100):
            from unittest.mock import AsyncMock

            from fastapi import WebSocket

            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"test-client-{i}"}
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()

            client_id = f"client_{i}"
            client_ids.append(client_id)
            mock_websockets.append(ws)

            await manager.connect(ws, client_id)

        connect_time = time.time() - start_time

        # Test broadcasting to all clients
        start_time = time.time()
        message = {"type": "test", "data": "performance test"}
        recipients = await manager.broadcast(message)
        broadcast_time = time.time() - start_time

        # Test disconnecting all clients
        start_time = time.time()
        for client_id in client_ids:
            await manager.disconnect(client_id)
        disconnect_time = time.time() - start_time

        # Performance assertions (adjust thresholds as needed)
        assert connect_time < 1.0, f"Connecting 100 clients took {connect_time:.2f}s"
        assert broadcast_time < 0.5, f"Broadcasting to 100 clients took {broadcast_time:.2f}s"
        assert disconnect_time < 0.5, f"Disconnecting 100 clients took {disconnect_time:.2f}s"
        assert recipients == 100, f"Expected 100 recipients, got {recipients}"

    @pytest.mark.asyncio
    async def test_notification_service_performance(self):
        """Test NotificationService performance."""
        from unittest.mock import AsyncMock

        # Mock connection manager
        mock_manager = AsyncMock()
        mock_manager.broadcast = AsyncMock(return_value=100)
        mock_manager.get_connection_count = AsyncMock(return_value=100)
        mock_manager.get_total_connections = AsyncMock(return_value=1000)

        service = NotificationService(mock_manager)

        # Test rapid notification sending
        start_time = time.time()

        tasks = []
        for i in range(50):
            task = service.send_notification({"message": f"Test {i}"})
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        send_time = time.time() - start_time

        # Performance assertions
        assert send_time < 2.0, f"Sending 50 notifications took {send_time:.2f}s"
        assert all(r == 100 for r in results), "Not all notifications were delivered"

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test handling concurrent connection attempts."""
        manager = ConnectionManager()

        async def connect_client(client_id):
            from unittest.mock import AsyncMock

            from fastapi import WebSocket

            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"test-client-{client_id}"}
            ws.accept = AsyncMock()

            try:
                await manager.connect(ws, f"client_{client_id}")
                return True
            except Exception:
                return False

        # Test concurrent connections
        start_time = time.time()

        tasks = [connect_client(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        concurrent_time = time.time() - start_time

        # Count successful connections
        successful = sum(1 for r in results if r is True)

        # Performance assertions
        assert concurrent_time < 2.0, f"50 concurrent connections took {concurrent_time:.2f}s"
        assert successful >= 45, f"Only {successful}/50 connections succeeded"

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively under load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        manager = ConnectionManager()

        # Create and destroy many connections
        for batch in range(10):
            # Connect 50 clients
            websockets = []
            client_ids = []

            for i in range(50):
                from unittest.mock import AsyncMock

                from fastapi import WebSocket

                ws = AsyncMock(spec=WebSocket)
                ws.headers = {"user-agent": f"test-client-{batch}-{i}"}
                ws.accept = AsyncMock()
                ws.send_json = AsyncMock()

                client_id = f"client_{batch}_{i}"
                client_ids.append(client_id)
                websockets.append(ws)

                await manager.connect(ws, client_id)

            # Broadcast some messages
            for _ in range(5):
                await manager.broadcast({"type": "test", "data": f"batch_{batch}"})

            # Disconnect all clients
            for client_id in client_ids:
                await manager.disconnect(client_id)

            # Force garbage collection
            import gc
            gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory should not grow excessively (allow some growth for test overhead)
        assert memory_growth < 50, f"Memory grew by {memory_growth:.2f}MB during load test"

    def test_http_endpoint_performance(self):
        """Test HTTP endpoint performance."""
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test health endpoint performance
        start_time = time.time()

        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200

        health_time = time.time() - start_time

        # Test notification endpoint performance
        notification_data = {
            "message": "Performance test notification",
            "type": "test"
        }

        start_time = time.time()

        for _ in range(50):
            response = client.post("/notify", json=notification_data)
            assert response.status_code == 200

        notify_time = time.time() - start_time

        # Performance assertions
        assert health_time < 5.0, f"100 health checks took {health_time:.2f}s"
        assert notify_time < 10.0, f"50 notifications took {notify_time:.2f}s"


class TestLoadTesting:
    """Load testing scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load(self):
        """Test server under sustained load."""
        # This test simulates sustained load over time
        # Mark as slow since it takes longer to run

        manager = ConnectionManager()

        # Simulate sustained connections
        active_connections = []

        try:
            # Gradually build up connections
            for i in range(200):
                from unittest.mock import AsyncMock

                from fastapi import WebSocket

                ws = AsyncMock(spec=WebSocket)
                ws.headers = {"user-agent": f"sustained-client-{i}"}
                ws.accept = AsyncMock()
                ws.send_json = AsyncMock()

                client_id = f"sustained_client_{i}"
                await manager.connect(ws, client_id)
                active_connections.append((ws, client_id))

                # Add small delay to simulate realistic connection pattern
                if i % 10 == 0:
                    await asyncio.sleep(0.1)

            # Maintain load for a period
            for round_num in range(10):
                # Broadcast messages
                message = {"type": "load_test", "round": round_num}
                recipients = await manager.broadcast(message)
                assert recipients == len(active_connections)

                # Simulate some disconnections and reconnections
                if round_num % 3 == 0:
                    # Disconnect 10% of clients
                    disconnect_count = len(active_connections) // 10
                    for _ in range(disconnect_count):
                        if active_connections:
                            ws, client_id = active_connections.pop()
                            await manager.disconnect(client_id)

                    # Reconnect new clients
                    for i in range(disconnect_count):
                        from unittest.mock import AsyncMock

                        from fastapi import WebSocket

                        ws = AsyncMock(spec=WebSocket)
                        ws.headers = {"user-agent": f"reconnect-client-{round_num}-{i}"}
                        ws.accept = AsyncMock()
                        ws.send_json = AsyncMock()

                        client_id = f"reconnect_client_{round_num}_{i}"
                        await manager.connect(ws, client_id)
                        active_connections.append((ws, client_id))

                await asyncio.sleep(0.5)  # Brief pause between rounds

        finally:
            # Clean up all connections
            for ws, client_id in active_connections:
                await manager.disconnect(client_id)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_connection_churn(self):
        """Test rapid connection and disconnection (churn)."""
        manager = ConnectionManager()

        # Test rapid connect/disconnect cycles
        for cycle in range(20):
            connections = []

            # Rapid connections
            connect_tasks = []
            for i in range(25):
                from unittest.mock import AsyncMock

                from fastapi import WebSocket

                ws = AsyncMock(spec=WebSocket)
                ws.headers = {"user-agent": f"churn-client-{cycle}-{i}"}
                ws.accept = AsyncMock()

                client_id = f"churn_client_{cycle}_{i}"
                connections.append((ws, client_id))

                task = manager.connect(ws, client_id)
                connect_tasks.append(task)

            # Wait for all connections
            await asyncio.gather(*connect_tasks)

            # Rapid disconnections
            disconnect_tasks = []
            for ws, client_id in connections:
                task = manager.disconnect(client_id)
                disconnect_tasks.append(task)

            # Wait for all disconnections
            await asyncio.gather(*disconnect_tasks)

            # Verify clean state
            assert await manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast_performance_scaling(self):
        """Test broadcast performance with increasing connection counts."""
        manager = ConnectionManager()

        connection_counts = [10, 50, 100, 200]
        broadcast_times = []

        for count in connection_counts:
            # Set up connections
            connections = []
            for i in range(count):
                from unittest.mock import AsyncMock

                from fastapi import WebSocket

                ws = AsyncMock(spec=WebSocket)
                ws.headers = {"user-agent": f"scale-client-{i}"}
                ws.accept = AsyncMock()
                ws.send_json = AsyncMock()

                client_id = f"scale_client_{i}"
                await manager.connect(ws, client_id)
                connections.append((ws, client_id))

            # Measure broadcast time
            message = {"type": "scale_test", "connection_count": count}

            start_time = time.time()
            recipients = await manager.broadcast(message)
            broadcast_time = time.time() - start_time

            broadcast_times.append(broadcast_time)

            assert recipients == count

            # Clean up
            for ws, client_id in connections:
                await manager.disconnect(client_id)

        # Verify broadcast time scales reasonably (should be roughly linear)
        # Allow for some variance in timing
        for i in range(1, len(broadcast_times)):
            ratio = broadcast_times[i] / broadcast_times[0]
            connection_ratio = connection_counts[i] / connection_counts[0]

            # Broadcast time should not grow faster than O(n log n)
            assert ratio < connection_ratio * 2, f"Broadcast time scaling poorly: {ratio} vs {connection_ratio}"


class TestStressScenarios:
    """Stress testing scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_maximum_connections(self):
        """Test behavior at maximum connection limit."""
        # Test with a smaller limit for testing
        with patch('websocket_server.config.settings.max_connections', 50):
            manager = ConnectionManager()

            connections = []

            # Connect up to the limit
            for i in range(50):
                from unittest.mock import AsyncMock

                from fastapi import WebSocket

                ws = AsyncMock(spec=WebSocket)
                ws.headers = {"user-agent": f"max-client-{i}"}
                ws.accept = AsyncMock()

                client_id = f"max_client_{i}"
                await manager.connect(ws, client_id)
                connections.append((ws, client_id))

            # Try to connect one more (should fail)
            ws_extra = AsyncMock(spec=WebSocket)
            ws_extra.headers = {"user-agent": "extra-client"}
            ws_extra.accept = AsyncMock()

            with pytest.raises(ValueError, match="Maximum connections exceeded"):
                await manager.connect(ws_extra, "extra_client")

            # Clean up
            for ws, client_id in connections:
                await manager.disconnect(client_id)

    @pytest.mark.asyncio
    @pytest.mark.stress
    async def test_rapid_message_broadcasting(self):
        """Test rapid message broadcasting."""
        manager = ConnectionManager()

        # Set up some connections
        connections = []
        for i in range(20):
            from unittest.mock import AsyncMock

            from fastapi import WebSocket

            ws = AsyncMock(spec=WebSocket)
            ws.headers = {"user-agent": f"rapid-client-{i}"}
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()

            client_id = f"rapid_client_{i}"
            await manager.connect(ws, client_id)
            connections.append((ws, client_id))

        # Rapid message broadcasting
        start_time = time.time()

        broadcast_tasks = []
        for i in range(100):
            message = {"type": "rapid_test", "message_id": i}
            task = manager.broadcast(message)
            broadcast_tasks.append(task)

        results = await asyncio.gather(*broadcast_tasks)

        broadcast_time = time.time() - start_time

        # Verify all broadcasts succeeded
        assert all(r == 20 for r in results), "Not all broadcasts succeeded"
        assert broadcast_time < 5.0, f"100 rapid broadcasts took {broadcast_time:.2f}s"

        # Clean up
        for ws, client_id in connections:
            await manager.disconnect(client_id)


# Utility functions for load testing

def run_load_test_scenario(scenario_func, *args, **kwargs):
    """Run a load test scenario and collect metrics."""
    import os

    import psutil

    process = psutil.Process(os.getpid())

    # Collect initial metrics
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    process.cpu_percent()

    start_time = time.time()

    # Run the scenario
    result = asyncio.run(scenario_func(*args, **kwargs))

    end_time = time.time()

    # Collect final metrics
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    final_cpu = process.cpu_percent()

    metrics = {
        "duration": end_time - start_time,
        "memory_growth": final_memory - initial_memory,
        "initial_memory": initial_memory,
        "final_memory": final_memory,
        "cpu_usage": final_cpu,
        "result": result
    }

    return metrics


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.performance,  # All tests in this file are performance tests
]

# Configuration for performance tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "stress: marks tests as stress tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


# Example usage:
# Run all performance tests: pytest tests/test_performance.py -v
# Run only fast tests: pytest tests/test_performance.py -v -m "not slow"
# Run stress tests: pytest tests/test_performance.py -v -m stress
