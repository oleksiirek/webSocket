"""Dependency injection for FastAPI."""

from .handlers import MultiWorkerShutdownCoordinator, ShutdownHandler
from .services import ConnectionManager, NotificationService

# Global service instances
connection_manager = ConnectionManager()
notification_service = NotificationService(connection_manager)
shutdown_handler = ShutdownHandler(connection_manager, notification_service)
multi_worker_coordinator = MultiWorkerShutdownCoordinator()


def get_connection_manager() -> ConnectionManager:
    """
    Dependency to get the connection manager instance.

    Returns:
        ConnectionManager instance
    """
    return connection_manager


def get_notification_service() -> NotificationService:
    """
    Dependency to get the notification service instance.

    Returns:
        NotificationService instance
    """
    return notification_service


def get_shutdown_handler() -> ShutdownHandler:
    """
    Dependency to get the shutdown handler instance.

    Returns:
        ShutdownHandler instance
    """
    return shutdown_handler


def get_multi_worker_coordinator() -> MultiWorkerShutdownCoordinator:
    """
    Dependency to get the multi-worker coordinator instance.

    Returns:
        MultiWorkerShutdownCoordinator instance
    """
    return multi_worker_coordinator
