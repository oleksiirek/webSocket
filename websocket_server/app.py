"""FastAPI application setup and configuration."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from loguru import logger

from .config import log_shutdown_info, log_startup_info, settings, setup_logging
from .dependencies import (
    connection_manager,
    multi_worker_coordinator,
    notification_service,
    shutdown_handler,
)
from .endpoints import (
    health_endpoint,
    metrics_endpoint,
    notify_endpoint,
    prometheus_metrics_endpoint,
    status_endpoint,
    websocket_endpoint,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    startup_time = datetime.now(UTC)

    try:
        # Setup logging first
        setup_logging()

        logger.info("Starting WebSocket Notification Server")

        # Setup multi-worker logging
        multi_worker_coordinator.setup_worker_logging()

        # Log startup information
        log_startup_info()

        # Register signal handlers for graceful shutdown
        shutdown_handler.register_signals()

        # Start notification service
        await notification_service.start_periodic_notifications()

        # Log startup completion
        logger.info(
            "WebSocket Notification Server started successfully",
            extra={
                "startup_time": startup_time.isoformat(),
                "worker_info": multi_worker_coordinator.get_worker_info(),
                "settings": {
                    "host": settings.host,
                    "port": settings.port,
                    "workers": settings.workers,
                    "max_connections": settings.max_connections,
                    "notification_interval": settings.notification_interval,
                    "shutdown_timeout": settings.shutdown_timeout
                }
            }
        )

        yield

    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise

    finally:
        # Shutdown
        logger.info("Shutting down WebSocket Notification Server")
        log_shutdown_info()

        try:
            # Coordinate shutdown across workers
            await multi_worker_coordinator.coordinate_shutdown(
                shutdown_handler,
                connection_manager,
                notification_service
            )

            # Cleanup services
            await notification_service.cleanup()
            await shutdown_handler.cleanup()

            logger.info("WebSocket Notification Server shutdown completed")

        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="WebSocket Notification Server",
        description="Production-ready WebSocket notification server built with FastAPI",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    # Add middleware for CORS if needed
    if settings.debug:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Add WebSocket route
    app.websocket("/ws")(websocket_endpoint)

    # Add HTTP routes
    app.get("/health")(health_endpoint)
    app.post("/notify")(notify_endpoint)
    app.get("/metrics")(metrics_endpoint)
    app.get("/metrics/prometheus")(prometheus_metrics_endpoint)
    app.get("/status")(status_endpoint)

    return app





# Create the FastAPI application
app = create_app()
