"""Graceful shutdown handler for the WebSocket server."""

import asyncio
import signal
import sys
from datetime import UTC, datetime, timedelta

from loguru import logger

from ..config import settings
from ..services import ConnectionManager, NotificationService


class ShutdownHandler:
    """Handles graceful application shutdown with connection monitoring."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        notification_service: NotificationService
    ):
        """
        Initialize the shutdown handler.

        Args:
            connection_manager: ConnectionManager instance
            notification_service: NotificationService instance
        """
        self.connection_manager = connection_manager
        self.notification_service = notification_service
        self._shutdown_requested = False
        self._shutdown_start_time: datetime | None = None
        self._original_handlers: dict = {}

    def register_signals(self) -> None:
        """Register signal handlers for graceful shutdown."""
        # Store original handlers for restoration if needed
        self._original_handlers = {
            signal.SIGTERM: signal.signal(signal.SIGTERM, self._signal_handler),
            signal.SIGINT: signal.signal(signal.SIGINT, self._signal_handler),
        }

        # On Windows, SIGTERM might not be available
        if sys.platform == "win32":
            try:
                signal.signal(signal.SIGBREAK, self._signal_handler)
            except AttributeError:
                pass  # SIGBREAK not available on all Windows versions

        logger.info(
            "Registered signal handlers for graceful shutdown",
            extra={"signals": ["SIGTERM", "SIGINT"]}
        )

    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name

        if self._shutdown_requested:
            logger.warning(
                f"Received {signal_name} during shutdown, forcing exit",
                extra={"signal": signal_name, "force_exit": True}
            )
            sys.exit(1)

        logger.info(
            f"Received {signal_name}, initiating graceful shutdown",
            extra={"signal": signal_name}
        )

        self._shutdown_requested = True
        self._shutdown_start_time = datetime.now(UTC)

        # Create a task to handle graceful shutdown
        asyncio.create_task(self.graceful_shutdown())

    async def graceful_shutdown(self) -> None:
        """
        Perform graceful shutdown sequence.
        """
        if not self._shutdown_requested:
            logger.warning("Graceful shutdown called without shutdown request")
            return

        logger.info(
            "Starting graceful shutdown sequence",
            extra={
                "shutdown_timeout": settings.shutdown_timeout,
                "start_time": self._shutdown_start_time.isoformat() if self._shutdown_start_time else None
            }
        )

        try:
            # Step 1: Stop accepting new connections and stop periodic notifications
            await self._stop_services()

            # Step 2: Notify connected clients about shutdown
            await self._notify_clients_shutdown()

            # Step 3: Wait for connections to close or timeout
            await self.wait_for_connections_or_timeout()

            # Step 4: Force close remaining connections
            await self._force_close_connections()

            logger.info("Graceful shutdown completed successfully")

        except Exception as e:
            logger.error(
                f"Error during graceful shutdown: {e}",
                extra={"error": str(e)}
            )
        finally:
            # Ensure we exit
            sys.exit(0)

    async def wait_for_connections_or_timeout(self) -> None:
        """
        Wait for connections to close naturally or until timeout.
        """
        if not self._shutdown_start_time:
            logger.error("Shutdown start time not set")
            return

        timeout_time = self._shutdown_start_time + timedelta(seconds=settings.shutdown_timeout)
        check_interval = 5  # Check every 5 seconds

        logger.info(
            f"Waiting for connections to close (timeout: {settings.shutdown_timeout}s)",
            extra={"timeout_seconds": settings.shutdown_timeout}
        )

        while datetime.now(UTC) < timeout_time:
            active_connections = await self.connection_manager.get_connection_count()

            if active_connections == 0:
                logger.info("All connections closed naturally")
                return

            remaining_time = (timeout_time - datetime.now(UTC)).total_seconds()

            logger.info(
                f"Waiting for {active_connections} connections to close "
                f"(remaining time: {remaining_time:.1f}s)",
                extra={
                    "active_connections": active_connections,
                    "remaining_time": remaining_time
                }
            )

            # Clean up any stale connections
            stale_cleaned = await self.connection_manager.cleanup_stale_connections()
            if stale_cleaned > 0:
                logger.info(f"Cleaned up {stale_cleaned} stale connections during shutdown")

            await asyncio.sleep(check_interval)

        # Timeout reached
        final_connections = await self.connection_manager.get_connection_count()
        logger.warning(
            f"Shutdown timeout reached with {final_connections} active connections",
            extra={
                "timeout_seconds": settings.shutdown_timeout,
                "remaining_connections": final_connections
            }
        )

    def is_shutdown_requested(self) -> bool:
        """
        Check if shutdown has been requested.

        Returns:
            True if shutdown was requested, False otherwise
        """
        return self._shutdown_requested

    def get_shutdown_info(self) -> dict:
        """
        Get information about the shutdown state.

        Returns:
            Dictionary with shutdown information
        """
        info = {
            "shutdown_requested": self._shutdown_requested,
            "shutdown_timeout": settings.shutdown_timeout
        }

        if self._shutdown_start_time:
            info["shutdown_start_time"] = self._shutdown_start_time.isoformat()
            elapsed = datetime.now(UTC) - self._shutdown_start_time
            info["elapsed_seconds"] = elapsed.total_seconds()
            info["remaining_seconds"] = max(0, settings.shutdown_timeout - elapsed.total_seconds())

        return info

    async def _stop_services(self) -> None:
        """Stop application services."""
        logger.info("Stopping application services")

        try:
            # Stop periodic notifications
            await self.notification_service.stop_periodic_notifications()
            logger.info("Stopped notification service")
        except Exception as e:
            logger.error(f"Error stopping notification service: {e}")

    async def _notify_clients_shutdown(self) -> None:
        """Notify connected clients about impending shutdown."""
        active_connections = await self.connection_manager.get_connection_count()

        if active_connections == 0:
            logger.info("No active connections to notify about shutdown")
            return

        logger.info(f"Notifying {active_connections} clients about shutdown")

        try:
            # Send shutdown notification
            recipients = await self.notification_service.send_system_notification(
                message="Server is shutting down. Please reconnect later.",
                priority="high"
            )

            logger.info(
                f"Shutdown notification sent to {recipients} clients",
                extra={"recipients": recipients}
            )

            # Give clients a moment to process the notification
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error notifying clients about shutdown: {e}")

    async def _force_close_connections(self) -> None:
        """Force close any remaining connections."""
        active_connections = await self.connection_manager.get_connection_count()

        if active_connections == 0:
            logger.info("No connections to force close")
            return

        logger.info(f"Force closing {active_connections} remaining connections")

        try:
            await self.connection_manager.shutdown_all_connections()

            # Verify all connections are closed
            final_count = await self.connection_manager.get_connection_count()
            if final_count > 0:
                logger.warning(f"{final_count} connections still active after force close")
            else:
                logger.info("All connections successfully closed")

        except Exception as e:
            logger.error(f"Error force closing connections: {e}")

    def restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._original_handlers.items():
            if handler is not None:
                signal.signal(sig, handler)

        logger.debug("Restored original signal handlers")

    async def cleanup(self) -> None:
        """Clean up the shutdown handler."""
        self.restore_signal_handlers()
        logger.debug("ShutdownHandler cleanup completed")
