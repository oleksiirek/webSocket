"""Multi-worker shutdown coordination utilities."""

import asyncio
import os
from datetime import UTC, datetime

from loguru import logger

from ..config import settings


class MultiWorkerShutdownCoordinator:
    """Coordinates graceful shutdown across multiple uvicorn workers."""

    def __init__(self):
        """Initialize the multi-worker shutdown coordinator."""
        self.worker_id = self._get_worker_id()
        self.is_master_worker = self._is_master_worker()

    def _get_worker_id(self) -> str:
        """
        Get the current worker ID.

        Returns:
            Worker identifier string
        """
        # Try to get worker ID from uvicorn environment
        worker_id = os.getenv("UVICORN_WORKER_ID")
        if worker_id:
            return f"worker-{worker_id}"

        # Fallback to process ID
        return f"pid-{os.getpid()}"

    def _is_master_worker(self) -> bool:
        """
        Determine if this is the master worker process.

        Returns:
            True if this is the master worker, False otherwise
        """
        # In single worker mode, always consider as master
        if settings.workers == 1:
            return True

        # Check if this is the first worker (master)
        worker_id = os.getenv("UVICORN_WORKER_ID", "0")
        return worker_id == "0" or worker_id == "1"

    def setup_worker_logging(self) -> None:
        """Configure worker-specific logging context."""
        # Add worker ID to all log records
        logger.configure(
            extra={
                "worker_id": self.worker_id,
                "is_master": self.is_master_worker,
                "total_workers": settings.workers
            }
        )

        logger.info(
            f"Worker {self.worker_id} initialized",
            extra={
                "worker_id": self.worker_id,
                "is_master": self.is_master_worker,
                "total_workers": settings.workers
            }
        )

    async def coordinate_shutdown(
        self,
        shutdown_handler,
        connection_manager,
        notification_service
    ) -> None:
        """
        Coordinate shutdown across multiple workers.

        Args:
            shutdown_handler: ShutdownHandler instance
            connection_manager: ConnectionManager instance
            notification_service: NotificationService instance
        """
        logger.info(
            f"Starting coordinated shutdown for {self.worker_id}",
            extra={
                "worker_id": self.worker_id,
                "is_master": self.is_master_worker
            }
        )

        try:
            if self.is_master_worker:
                await self._master_worker_shutdown(
                    shutdown_handler, connection_manager, notification_service
                )
            else:
                await self._worker_shutdown(
                    shutdown_handler, connection_manager, notification_service
                )
        except Exception as e:
            logger.error(
                f"Error during coordinated shutdown in {self.worker_id}: {e}",
                extra={"worker_id": self.worker_id, "error": str(e)}
            )
            raise

    async def _master_worker_shutdown(
        self,
        shutdown_handler,
        connection_manager,
        notification_service
    ) -> None:
        """
        Handle shutdown coordination as the master worker.

        Args:
            shutdown_handler: ShutdownHandler instance
            connection_manager: ConnectionManager instance
            notification_service: NotificationService instance
        """
        logger.info(
            "Master worker coordinating shutdown",
            extra={"worker_id": self.worker_id}
        )

        # Master worker handles the full graceful shutdown
        await shutdown_handler.graceful_shutdown()

    async def _worker_shutdown(
        self,
        shutdown_handler,
        connection_manager,
        notification_service
    ) -> None:
        """
        Handle shutdown as a regular worker.

        Args:
            shutdown_handler: ShutdownHandler instance
            connection_manager: ConnectionManager instance
            notification_service: NotificationService instance
        """
        logger.info(
            f"Worker {self.worker_id} performing local shutdown",
            extra={"worker_id": self.worker_id}
        )

        # Stop local services
        await shutdown_handler._stop_services()

        # Get local connection count
        local_connections = await connection_manager.get_connection_count()

        if local_connections > 0:
            logger.info(
                f"Worker {self.worker_id} has {local_connections} active connections",
                extra={
                    "worker_id": self.worker_id,
                    "local_connections": local_connections
                }
            )

            # Notify local clients
            await shutdown_handler._notify_clients_shutdown()

            # Wait for local connections with shorter timeout for workers
            await self._wait_for_local_connections(
                connection_manager,
                timeout_seconds=min(300, settings.shutdown_timeout // 2)  # Max 5 minutes or half of total timeout
            )

            # Force close remaining local connections
            await shutdown_handler._force_close_connections()

        logger.info(
            f"Worker {self.worker_id} shutdown completed",
            extra={"worker_id": self.worker_id}
        )

    async def _wait_for_local_connections(
        self,
        connection_manager,
        timeout_seconds: int
    ) -> None:
        """
        Wait for local connections to close with timeout.

        Args:
            connection_manager: ConnectionManager instance
            timeout_seconds: Maximum time to wait
        """
        start_time = datetime.now(UTC)
        check_interval = 2  # Check every 2 seconds for workers

        logger.info(
            f"Worker {self.worker_id} waiting for local connections (timeout: {timeout_seconds}s)",
            extra={
                "worker_id": self.worker_id,
                "timeout_seconds": timeout_seconds
            }
        )

        while True:
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                break

            local_connections = await connection_manager.get_connection_count()
            if local_connections == 0:
                logger.info(
                    f"Worker {self.worker_id} - all local connections closed",
                    extra={"worker_id": self.worker_id}
                )
                return

            remaining_time = timeout_seconds - elapsed
            logger.debug(
                f"Worker {self.worker_id} - {local_connections} connections remaining "
                f"(timeout in {remaining_time:.1f}s)",
                extra={
                    "worker_id": self.worker_id,
                    "local_connections": local_connections,
                    "remaining_time": remaining_time
                }
            )

            await asyncio.sleep(check_interval)

        # Timeout reached
        final_connections = await connection_manager.get_connection_count()
        if final_connections > 0:
            logger.warning(
                f"Worker {self.worker_id} timeout reached with {final_connections} connections",
                extra={
                    "worker_id": self.worker_id,
                    "remaining_connections": final_connections
                }
            )

    def get_worker_info(self) -> dict:
        """
        Get information about the current worker.

        Returns:
            Dictionary with worker information
        """
        return {
            "worker_id": self.worker_id,
            "is_master": self.is_master_worker,
            "total_workers": settings.workers,
            "process_id": os.getpid(),
            "uvicorn_worker_id": os.getenv("UVICORN_WORKER_ID")
        }
