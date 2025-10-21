"""Notification service for managing and broadcasting messages."""

import asyncio
from datetime import UTC, datetime

from loguru import logger

from ..config import settings
from ..models import NotificationMessage
from .connection_manager import ConnectionManager


class NotificationService:
    """Service for managing periodic and on-demand notifications."""

    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize the notification service.

        Args:
            connection_manager: ConnectionManager instance for broadcasting
        """
        self.connection_manager = connection_manager
        self._periodic_task: asyncio.Task | None = None
        self._is_running = False
        self._notification_counter = 0
        self._start_time = datetime.now(UTC)

    async def start_periodic_notifications(self) -> None:
        """Start the periodic notification task."""
        if self._is_running:
            logger.warning("Periodic notifications already running")
            return

        self._is_running = True
        self._periodic_task = asyncio.create_task(self._periodic_notification_loop())

        logger.info(
            f"Started periodic notifications (interval: {settings.notification_interval}s)",
            extra={"notification_interval": settings.notification_interval}
        )

    async def stop_periodic_notifications(self) -> None:
        """Stop the periodic notification task."""
        if not self._is_running:
            logger.debug("Periodic notifications not running")
            return

        self._is_running = False

        if self._periodic_task and not self._periodic_task.done():
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass

        logger.info(
            "Stopped periodic notifications",
            extra={"total_notifications_sent": self._notification_counter}
        )

    async def send_notification(self, message: dict) -> int:
        """
        Send a notification message to all connected clients.

        Args:
            message: Message dictionary to broadcast

        Returns:
            Number of clients that received the message
        """
        try:
            # Create a proper notification message if not already formatted
            if not isinstance(message, dict) or "id" not in message:
                notification = NotificationMessage(
                    data=message if isinstance(message, dict) else {"message": str(message)}
                )
                message_dict = notification.model_dump(mode='json')
            else:
                message_dict = message

            # Broadcast the message
            recipients = await self.connection_manager.broadcast(message_dict)

            logger.info(
                f"Notification sent to {recipients} clients",
                extra={
                    "recipients": recipients,
                    "message_type": message_dict.get("type", "unknown"),
                    "message_id": message_dict.get("id")
                }
            )

            return recipients

        except Exception as e:
            logger.error(
                f"Failed to send notification: {e}",
                extra={"error": str(e), "message": message}
            )
            return 0

    async def create_test_notification(self) -> dict:
        """
        Create a test notification message with proper structure.

        Returns:
            Dictionary containing the test notification
        """
        self._notification_counter += 1
        uptime = datetime.now(UTC) - self._start_time

        notification = NotificationMessage(
            type="test_notification",
            data={
                "message": f"Test notification #{self._notification_counter}",
                "counter": self._notification_counter,
                "uptime_seconds": uptime.total_seconds(),
                "active_connections": await self.connection_manager.get_connection_count(),
                "server_time": datetime.now(UTC).isoformat()
            },
            sender="notification_service"
        )

        return notification.model_dump(mode='json')

    async def send_test_notification(self) -> int:
        """
        Create and send a test notification.

        Returns:
            Number of clients that received the notification
        """
        test_message = await self.create_test_notification()
        return await self.send_notification(test_message)

    async def send_custom_notification(
        self,
        message: str,
        notification_type: str = "custom",
        data: dict | None = None
    ) -> int:
        """
        Send a custom notification with specified content.

        Args:
            message: The notification message content
            notification_type: Type of notification
            data: Additional data to include

        Returns:
            Number of clients that received the notification
        """
        notification_data = {"message": message}
        if data:
            notification_data.update(data)

        notification = NotificationMessage(
            type=notification_type,
            data=notification_data,
            sender="notification_service"
        )

        return await self.send_notification(notification.model_dump(mode='json'))

    async def send_system_notification(
        self,
        message: str,
        priority: str = "normal"
    ) -> int:
        """
        Send a system notification (e.g., maintenance, alerts).

        Args:
            message: System message content
            priority: Priority level (low, normal, high, critical)

        Returns:
            Number of clients that received the notification
        """
        notification = NotificationMessage(
            type="system",
            data={
                "message": message,
                "priority": priority,
                "system_time": datetime.now(UTC).isoformat()
            },
            sender="system"
        )

        return await self.send_notification(notification.model_dump(mode='json'))

    async def get_service_stats(self) -> dict:
        """
        Get notification service statistics.

        Returns:
            Dictionary containing service statistics
        """
        uptime = datetime.now(UTC) - self._start_time
        active_connections = await self.connection_manager.get_connection_count()
        total_connections = await self.connection_manager.get_total_connections()

        return {
            "is_running": self._is_running,
            "notifications_sent": self._notification_counter,
            "uptime_seconds": uptime.total_seconds(),
            "active_connections": active_connections,
            "total_connections": total_connections,
            "notification_interval": settings.notification_interval,
            "start_time": self._start_time.isoformat()
        }

    async def _periodic_notification_loop(self) -> None:
        """Internal method for the periodic notification loop."""
        logger.debug("Starting periodic notification loop")

        try:
            while self._is_running:
                # Send test notification
                recipients = await self.send_test_notification()

                logger.debug(
                    f"Periodic notification sent to {recipients} clients",
                    extra={
                        "recipients": recipients,
                        "notification_number": self._notification_counter
                    }
                )

                # Wait for next interval
                await asyncio.sleep(settings.notification_interval)

        except asyncio.CancelledError:
            logger.debug("Periodic notification loop cancelled")
            raise
        except Exception as e:
            logger.error(
                f"Error in periodic notification loop: {e}",
                extra={"error": str(e)}
            )
            self._is_running = False
            raise
        finally:
            logger.debug("Periodic notification loop ended")

    async def cleanup(self) -> None:
        """Clean up the notification service."""
        await self.stop_periodic_notifications()

        logger.info(
            "NotificationService cleanup completed",
            extra={"total_notifications": self._notification_counter}
        )
