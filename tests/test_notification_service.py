"""Unit tests for NotificationService."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from websocket_server.services.connection_manager import ConnectionManager
from websocket_server.services.notification_service import NotificationService


@pytest.fixture
def mock_connection_manager():
    """Create a mock ConnectionManager for testing."""
    manager = AsyncMock(spec=ConnectionManager)
    manager.broadcast = AsyncMock(return_value=5)  # Default 5 recipients
    manager.get_connection_count = AsyncMock(return_value=5)
    manager.get_total_connections = AsyncMock(return_value=100)
    return manager


@pytest.fixture
def notification_service(mock_connection_manager):
    """Create a NotificationService instance for testing."""
    return NotificationService(mock_connection_manager)


class TestNotificationService:
    """Test cases for NotificationService."""

    @pytest.mark.asyncio
    async def test_start_periodic_notifications(self, notification_service):
        """Test starting periodic notifications."""
        assert not notification_service._is_running

        # Start periodic notifications
        await notification_service.start_periodic_notifications()

        assert notification_service._is_running
        assert notification_service._periodic_task is not None

        # Clean up
        await notification_service.stop_periodic_notifications()

    @pytest.mark.asyncio
    async def test_start_periodic_notifications_already_running(self, notification_service):
        """Test starting periodic notifications when already running."""
        # Start first time
        await notification_service.start_periodic_notifications()

        # Try to start again - should not create new task
        old_task = notification_service._periodic_task
        await notification_service.start_periodic_notifications()

        # Task should be the same
        assert notification_service._periodic_task == old_task

        # Clean up
        await notification_service.stop_periodic_notifications()

    @pytest.mark.asyncio
    async def test_stop_periodic_notifications(self, notification_service):
        """Test stopping periodic notifications."""
        # Start notifications
        await notification_service.start_periodic_notifications()
        assert notification_service._is_running

        # Stop notifications
        await notification_service.stop_periodic_notifications()
        assert not notification_service._is_running

    @pytest.mark.asyncio
    async def test_stop_periodic_notifications_not_running(self, notification_service):
        """Test stopping periodic notifications when not running."""
        # Should not raise an error
        await notification_service.stop_periodic_notifications()
        assert not notification_service._is_running

    @pytest.mark.asyncio
    async def test_send_notification_dict(self, notification_service, mock_connection_manager):
        """Test sending a notification with dictionary input."""
        message = {"message": "Test notification", "priority": "high"}

        recipients = await notification_service.send_notification(message)

        assert recipients == 5
        mock_connection_manager.broadcast.assert_called_once()

        # Verify the message was properly formatted
        call_args = mock_connection_manager.broadcast.call_args[0][0]
        assert "id" in call_args
        assert "type" in call_args
        assert "timestamp" in call_args
        assert call_args["data"] == message

    @pytest.mark.asyncio
    async def test_send_notification_string(self, notification_service, mock_connection_manager):
        """Test sending a notification with string input."""
        message = "Simple test message"

        recipients = await notification_service.send_notification(message)

        assert recipients == 5
        mock_connection_manager.broadcast.assert_called_once()

        # Verify the message was properly formatted
        call_args = mock_connection_manager.broadcast.call_args[0][0]
        assert call_args["data"]["message"] == message

    @pytest.mark.asyncio
    async def test_send_notification_error(self, notification_service, mock_connection_manager):
        """Test sending notification when broadcast fails."""
        mock_connection_manager.broadcast.side_effect = Exception("Broadcast failed")

        recipients = await notification_service.send_notification({"test": "message"})

        assert recipients == 0

    @pytest.mark.asyncio
    async def test_create_test_notification(self, notification_service):
        """Test creating a test notification."""
        notification = await notification_service.create_test_notification()

        assert notification["type"] == "test_notification"
        assert notification["sender"] == "notification_service"
        assert "id" in notification
        assert "timestamp" in notification
        assert "data" in notification

        # Verify data content
        data = notification["data"]
        assert "message" in data
        assert "counter" in data
        assert "uptime_seconds" in data
        assert "active_connections" in data
        assert "server_time" in data

    @pytest.mark.asyncio
    async def test_send_test_notification(self, notification_service, mock_connection_manager):
        """Test sending a test notification."""
        recipients = await notification_service.send_test_notification()

        assert recipients == 5
        mock_connection_manager.broadcast.assert_called_once()

        # Verify it was a test notification
        call_args = mock_connection_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "test_notification"
        assert call_args["sender"] == "notification_service"

    @pytest.mark.asyncio
    async def test_send_custom_notification(self, notification_service, mock_connection_manager):
        """Test sending a custom notification."""
        message = "Custom message"
        notification_type = "alert"
        data = {"priority": "high", "category": "system"}

        recipients = await notification_service.send_custom_notification(
            message, notification_type, data
        )

        assert recipients == 5
        mock_connection_manager.broadcast.assert_called_once()

        # Verify the notification format
        call_args = mock_connection_manager.broadcast.call_args[0][0]
        assert call_args["type"] == notification_type
        assert call_args["sender"] == "notification_service"
        assert call_args["data"]["message"] == message
        assert call_args["data"]["priority"] == "high"
        assert call_args["data"]["category"] == "system"

    @pytest.mark.asyncio
    async def test_send_system_notification(self, notification_service, mock_connection_manager):
        """Test sending a system notification."""
        message = "System maintenance"
        priority = "critical"

        recipients = await notification_service.send_system_notification(message, priority)

        assert recipients == 5
        mock_connection_manager.broadcast.assert_called_once()

        # Verify the notification format
        call_args = mock_connection_manager.broadcast.call_args[0][0]
        assert call_args["type"] == "system"
        assert call_args["sender"] == "system"
        assert call_args["data"]["message"] == message
        assert call_args["data"]["priority"] == priority

    @pytest.mark.asyncio
    async def test_get_service_stats(self, notification_service, mock_connection_manager):
        """Test getting service statistics."""
        # Send a test notification to increment counter
        await notification_service.send_test_notification()

        stats = await notification_service.get_service_stats()

        assert "is_running" in stats
        assert "notifications_sent" in stats
        assert "uptime_seconds" in stats
        assert "active_connections" in stats
        assert "total_connections" in stats
        assert "notification_interval" in stats
        assert "start_time" in stats

        assert stats["notifications_sent"] == 1
        assert stats["active_connections"] == 5
        assert stats["total_connections"] == 100

    @pytest.mark.asyncio
    async def test_cleanup(self, notification_service):
        """Test service cleanup."""
        # Start notifications
        await notification_service.start_periodic_notifications()
        assert notification_service._is_running

        # Cleanup
        await notification_service.cleanup()

        assert not notification_service._is_running

    @pytest.mark.asyncio
    async def test_notification_counter_increment(self, notification_service):
        """Test that notification counter increments correctly."""
        initial_stats = await notification_service.get_service_stats()
        initial_count = initial_stats["notifications_sent"]

        # Send multiple notifications
        await notification_service.send_test_notification()
        await notification_service.send_test_notification()

        final_stats = await notification_service.get_service_stats()
        final_count = final_stats["notifications_sent"]

        assert final_count == initial_count + 2

    @pytest.mark.asyncio
    async def test_periodic_notification_loop_short_run(self, notification_service, mock_connection_manager):
        """Test periodic notification loop runs correctly."""
        # Mock settings to have a very short interval for testing
        with patch('websocket_server.services.notification_service.settings') as mock_settings:
            mock_settings.notification_interval = 0.1  # 100ms for fast testing

            # Start periodic notifications
            await notification_service.start_periodic_notifications()

            # Wait a short time for at least one notification
            await asyncio.sleep(0.2)

            # Stop notifications
            await notification_service.stop_periodic_notifications()

            # Verify at least one broadcast was made
            assert mock_connection_manager.broadcast.call_count >= 1
