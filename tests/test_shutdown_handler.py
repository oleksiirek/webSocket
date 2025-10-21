"""Unit tests for ShutdownHandler."""

import signal
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from websocket_server.handlers.shutdown_handler import ShutdownHandler
from websocket_server.services.connection_manager import ConnectionManager
from websocket_server.services.notification_service import NotificationService


@pytest.fixture
def mock_connection_manager():
    """Create a mock ConnectionManager for testing."""
    manager = AsyncMock(spec=ConnectionManager)
    manager.get_connection_count = AsyncMock(return_value=0)
    manager.cleanup_stale_connections = AsyncMock(return_value=0)
    manager.shutdown_all_connections = AsyncMock()
    return manager


@pytest.fixture
def mock_notification_service():
    """Create a mock NotificationService for testing."""
    service = AsyncMock(spec=NotificationService)
    service.stop_periodic_notifications = AsyncMock()
    service.send_system_notification = AsyncMock(return_value=5)
    return service


@pytest.fixture
def shutdown_handler(mock_connection_manager, mock_notification_service):
    """Create a ShutdownHandler instance for testing."""
    return ShutdownHandler(mock_connection_manager, mock_notification_service)


class TestShutdownHandler:
    """Test cases for ShutdownHandler."""

    def test_register_signals(self, shutdown_handler):
        """Test signal registration."""
        with patch('signal.signal') as mock_signal:
            shutdown_handler.register_signals()

            # Verify SIGTERM and SIGINT handlers were registered
            assert mock_signal.call_count >= 2

            # Check that SIGTERM and SIGINT were registered
            calls = mock_signal.call_args_list
            registered_signals = [call[0][0] for call in calls]
            assert signal.SIGTERM in registered_signals
            assert signal.SIGINT in registered_signals

    def test_signal_handler_first_signal(self, shutdown_handler):
        """Test signal handler on first signal."""
        assert not shutdown_handler.is_shutdown_requested()

        with patch.object(shutdown_handler, 'graceful_shutdown'):
            with patch('asyncio.create_task') as mock_create_task:
                # Simulate receiving SIGTERM
                shutdown_handler._signal_handler(signal.SIGTERM, None)

                assert shutdown_handler.is_shutdown_requested()
                assert shutdown_handler._shutdown_start_time is not None
                mock_create_task.assert_called_once()

    def test_signal_handler_second_signal(self, shutdown_handler):
        """Test signal handler on second signal (force exit)."""
        # Set shutdown as already requested
        shutdown_handler._shutdown_requested = True

        with patch('sys.exit') as mock_exit:
            # Simulate receiving second signal
            shutdown_handler._signal_handler(signal.SIGTERM, None)

            mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_graceful_shutdown_no_connections(self, shutdown_handler, mock_connection_manager, mock_notification_service):
        """Test graceful shutdown with no active connections."""
        # Set up shutdown state
        shutdown_handler._shutdown_requested = True
        shutdown_handler._shutdown_start_time = datetime.now(UTC)

        # No active connections
        mock_connection_manager.get_connection_count.return_value = 0

        with patch('sys.exit') as mock_exit:
            await shutdown_handler.graceful_shutdown()

            # Verify services were stopped
            mock_notification_service.stop_periodic_notifications.assert_called_once()

            # Verify system notification was sent
            mock_notification_service.send_system_notification.assert_called_once()

            # Verify exit was called
            mock_exit.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_graceful_shutdown_with_connections(self, shutdown_handler, mock_connection_manager, mock_notification_service):
        """Test graceful shutdown with active connections."""
        # Set up shutdown state
        shutdown_handler._shutdown_requested = True
        shutdown_handler._shutdown_start_time = datetime.now(UTC)

        # Mock connections that will close after first check
        connection_counts = [2, 0]  # 2 connections, then 0
        mock_connection_manager.get_connection_count.side_effect = connection_counts

        with patch('sys.exit') as mock_exit:
            with patch('asyncio.sleep'):
                await shutdown_handler.graceful_shutdown()

                # Verify services were stopped
                mock_notification_service.stop_periodic_notifications.assert_called_once()

                # Verify system notification was sent
                mock_notification_service.send_system_notification.assert_called_once()

                # Verify exit was called
                mock_exit.assert_called_once_with(0)

    @pytest.mark.asyncio
    async def test_wait_for_connections_or_timeout_no_connections(self, shutdown_handler, mock_connection_manager):
        """Test waiting for connections when there are none."""
        shutdown_handler._shutdown_start_time = datetime.now(UTC)
        mock_connection_manager.get_connection_count.return_value = 0

        # Should return immediately
        await shutdown_handler.wait_for_connections_or_timeout()

        # Should have checked connection count at least once
        mock_connection_manager.get_connection_count.assert_called()

    @pytest.mark.asyncio
    async def test_wait_for_connections_or_timeout_with_timeout(self, shutdown_handler, mock_connection_manager):
        """Test waiting for connections with timeout."""
        # Set shutdown time to past (simulate timeout)
        shutdown_handler._shutdown_start_time = datetime.now(UTC) - timedelta(seconds=3700)  # Over 1 hour ago
        mock_connection_manager.get_connection_count.return_value = 5  # Still have connections

        with patch('websocket_server.handlers.shutdown_handler.settings') as mock_settings:
            mock_settings.shutdown_timeout = 3600  # 1 hour

            # Should timeout immediately due to past start time
            await shutdown_handler.wait_for_connections_or_timeout()

            # Should have checked connection count
            mock_connection_manager.get_connection_count.assert_called()

    def test_is_shutdown_requested_false(self, shutdown_handler):
        """Test is_shutdown_requested when shutdown not requested."""
        assert not shutdown_handler.is_shutdown_requested()

    def test_is_shutdown_requested_true(self, shutdown_handler):
        """Test is_shutdown_requested when shutdown is requested."""
        shutdown_handler._shutdown_requested = True
        assert shutdown_handler.is_shutdown_requested()

    def test_get_shutdown_info_not_requested(self, shutdown_handler):
        """Test get_shutdown_info when shutdown not requested."""
        info = shutdown_handler.get_shutdown_info()

        assert info["shutdown_requested"] is False
        assert "shutdown_timeout" in info
        assert "shutdown_start_time" not in info

    def test_get_shutdown_info_requested(self, shutdown_handler):
        """Test get_shutdown_info when shutdown is requested."""
        shutdown_handler._shutdown_requested = True
        shutdown_handler._shutdown_start_time = datetime.now(UTC)

        info = shutdown_handler.get_shutdown_info()

        assert info["shutdown_requested"] is True
        assert "shutdown_timeout" in info
        assert "shutdown_start_time" in info
        assert "elapsed_seconds" in info
        assert "remaining_seconds" in info

    @pytest.mark.asyncio
    async def test_stop_services(self, shutdown_handler, mock_notification_service):
        """Test stopping application services."""
        await shutdown_handler._stop_services()

        mock_notification_service.stop_periodic_notifications.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_clients_shutdown_no_connections(self, shutdown_handler, mock_connection_manager, mock_notification_service):
        """Test notifying clients about shutdown when no connections."""
        mock_connection_manager.get_connection_count.return_value = 0

        await shutdown_handler._notify_clients_shutdown()

        # Should not send notification if no connections
        mock_notification_service.send_system_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_clients_shutdown_with_connections(self, shutdown_handler, mock_connection_manager, mock_notification_service):
        """Test notifying clients about shutdown with active connections."""
        mock_connection_manager.get_connection_count.return_value = 5

        with patch('asyncio.sleep') as mock_sleep:
            await shutdown_handler._notify_clients_shutdown()

            # Should send shutdown notification
            mock_notification_service.send_system_notification.assert_called_once_with(
                message="Server is shutting down. Please reconnect later.",
                priority="high"
            )

            # Should wait briefly for clients to process
            mock_sleep.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_force_close_connections_no_connections(self, shutdown_handler, mock_connection_manager):
        """Test force closing connections when none exist."""
        mock_connection_manager.get_connection_count.return_value = 0

        await shutdown_handler._force_close_connections()

        # Should not call shutdown if no connections
        mock_connection_manager.shutdown_all_connections.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_close_connections_with_connections(self, shutdown_handler, mock_connection_manager):
        """Test force closing connections when they exist."""
        # Mock connection counts: 5 before shutdown, 0 after
        mock_connection_manager.get_connection_count.side_effect = [5, 0]

        await shutdown_handler._force_close_connections()

        # Should call shutdown_all_connections
        mock_connection_manager.shutdown_all_connections.assert_called_once()

    def test_restore_signal_handlers(self, shutdown_handler):
        """Test restoring original signal handlers."""
        # Set up some mock original handlers
        shutdown_handler._original_handlers = {
            signal.SIGTERM: MagicMock(),
            signal.SIGINT: MagicMock()
        }

        with patch('signal.signal') as mock_signal:
            shutdown_handler.restore_signal_handlers()

            # Should restore both handlers
            assert mock_signal.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup(self, shutdown_handler):
        """Test cleanup method."""
        with patch.object(shutdown_handler, 'restore_signal_handlers') as mock_restore:
            await shutdown_handler.cleanup()

            mock_restore.assert_called_once()

    @pytest.mark.asyncio
    async def test_graceful_shutdown_error_handling(self, shutdown_handler, mock_connection_manager, mock_notification_service):
        """Test graceful shutdown handles errors properly."""
        # Set up shutdown state
        shutdown_handler._shutdown_requested = True
        shutdown_handler._shutdown_start_time = datetime.now(UTC)

        # Make stop_services raise an exception
        mock_notification_service.stop_periodic_notifications.side_effect = Exception("Service error")

        with patch('sys.exit') as mock_exit:
            await shutdown_handler.graceful_shutdown()

            # Should still exit even with errors
            mock_exit.assert_called_once_with(0)
