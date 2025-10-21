"""HTTP endpoint implementations."""

from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from loguru import logger

from ..config import settings
from ..dependencies import (
    get_connection_manager,
    get_notification_service,
    get_shutdown_handler,
)
from ..handlers import ShutdownHandler
from ..models import BroadcastRequest, ConnectionStats
from ..services import ConnectionManager, NotificationService


async def health_endpoint(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    shutdown_handler: ShutdownHandler = Depends(get_shutdown_handler)
) -> JSONResponse:
    """
    Health check endpoint for monitoring systems.

    Args:
        connection_manager: ConnectionManager dependency
        shutdown_handler: ShutdownHandler dependency

    Returns:
        JSON response with health status
    """
    try:
        # Check if shutdown is in progress
        if shutdown_handler.is_shutdown_requested():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "shutting_down",
                    "message": "Server is shutting down",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "shutdown_info": shutdown_handler.get_shutdown_info()
                }
            )

        # Get connection statistics
        active_connections = await connection_manager.get_connection_count()
        total_connections = await connection_manager.get_total_connections()

        # Determine health status
        health_status = "healthy"
        if active_connections >= settings.max_connections * 0.9:  # 90% capacity
            health_status = "warning"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": health_status,
                "message": "WebSocket Notification Server is running",
                "timestamp": datetime.now(UTC).isoformat(),
                "connections": {
                    "active": active_connections,
                    "total": total_connections,
                    "max_allowed": settings.max_connections
                },
                "server_info": {
                    "version": "0.1.0",
                    "workers": settings.workers,
                    "notification_interval": settings.notification_interval
                }
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now(UTC).isoformat()
            }
        )


async def notify_endpoint(
    request: BroadcastRequest,
    notification_service: NotificationService = Depends(get_notification_service),
    shutdown_handler: ShutdownHandler = Depends(get_shutdown_handler)
) -> JSONResponse:
    """
    Endpoint for broadcasting on-demand notifications.

    Args:
        request: Broadcast request data
        notification_service: NotificationService dependency
        shutdown_handler: ShutdownHandler dependency

    Returns:
        JSON response with broadcast results
    """
    # Check if shutdown is in progress
    if shutdown_handler.is_shutdown_requested():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is shutting down, cannot send notifications"
        )

    try:
        logger.info(
            f"Manual notification request: {request.message}",
            extra={
                "message_type": request.type,
                "message_length": len(request.message)
            }
        )

        # Send the notification
        recipients = await notification_service.send_custom_notification(
            message=request.message,
            notification_type=request.type,
            data=request.data
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Notification sent successfully",
                "recipients": recipients,
                "notification": {
                    "message": request.message,
                    "type": request.type,
                    "data": request.data
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        ) from e


async def metrics_endpoint(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    notification_service: NotificationService = Depends(get_notification_service)
) -> JSONResponse:
    """
    Metrics endpoint for monitoring and statistics.

    Args:
        connection_manager: ConnectionManager dependency
        notification_service: NotificationService dependency

    Returns:
        JSON response with server metrics
    """
    try:
        # Get service statistics
        service_stats = await notification_service.get_service_stats()

        # Create connection stats model
        connection_stats = ConnectionStats(
            active_connections=service_stats["active_connections"],
            total_connections=service_stats["total_connections"],
            messages_sent=service_stats["notifications_sent"],
            uptime_seconds=service_stats["uptime_seconds"]
        )

        # Additional metrics
        metrics = {
            "connections": connection_stats.model_dump(),
            "notification_service": {
                "is_running": service_stats["is_running"],
                "notification_interval": service_stats["notification_interval"],
                "start_time": service_stats["start_time"]
            },
            "server": {
                "version": "0.1.0",
                "workers": settings.workers,
                "max_connections": settings.max_connections,
                "debug_mode": settings.debug
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=metrics
        )

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        ) from e


async def prometheus_metrics_endpoint(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    notification_service: NotificationService = Depends(get_notification_service)
) -> PlainTextResponse:
    """
    Prometheus-compatible metrics endpoint.

    Args:
        connection_manager: ConnectionManager dependency
        notification_service: NotificationService dependency

    Returns:
        Plain text response with Prometheus metrics
    """
    try:
        # Get service statistics
        service_stats = await notification_service.get_service_stats()

        # Generate Prometheus metrics format
        metrics_text = f"""# HELP websocket_active_connections Number of active WebSocket connections
# TYPE websocket_active_connections gauge
websocket_active_connections {service_stats["active_connections"]}

# HELP websocket_total_connections Total number of connections since server start
# TYPE websocket_total_connections counter
websocket_total_connections {service_stats["total_connections"]}

# HELP websocket_notifications_sent Total number of notifications sent
# TYPE websocket_notifications_sent counter
websocket_notifications_sent {service_stats["notifications_sent"]}

# HELP websocket_server_uptime_seconds Server uptime in seconds
# TYPE websocket_server_uptime_seconds gauge
websocket_server_uptime_seconds {service_stats["uptime_seconds"]}

# HELP websocket_notification_service_running Notification service running status (1=running, 0=stopped)
# TYPE websocket_notification_service_running gauge
websocket_notification_service_running {1 if service_stats["is_running"] else 0}

# HELP websocket_max_connections Maximum allowed connections
# TYPE websocket_max_connections gauge
websocket_max_connections {settings.max_connections}

# HELP websocket_workers Number of worker processes
# TYPE websocket_workers gauge
websocket_workers {settings.workers}
"""

        return PlainTextResponse(
            content=metrics_text,
            media_type="text/plain"
        )

    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate metrics: {str(e)}"
        ) from e


async def status_endpoint(
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    notification_service: NotificationService = Depends(get_notification_service),
    shutdown_handler: ShutdownHandler = Depends(get_shutdown_handler)
) -> JSONResponse:
    """
    Detailed status endpoint with comprehensive server information.

    Args:
        connection_manager: ConnectionManager dependency
        notification_service: NotificationService dependency
        shutdown_handler: ShutdownHandler dependency

    Returns:
        JSON response with detailed status information
    """
    try:
        # Get all service statistics
        service_stats = await notification_service.get_service_stats()
        shutdown_info = shutdown_handler.get_shutdown_info()

        # Get all connection info
        all_connections = await connection_manager.get_all_connection_info()

        status_info = {
            "server": {
                "status": "shutting_down" if shutdown_info["shutdown_requested"] else "running",
                "version": "0.1.0",
                "uptime_seconds": service_stats["uptime_seconds"],
                "start_time": service_stats["start_time"],
                "current_time": datetime.now(UTC).isoformat()
            },
            "connections": {
                "active": service_stats["active_connections"],
                "total": service_stats["total_connections"],
                "max_allowed": settings.max_connections,
                "details": [
                    {
                        "client_id": info.client_id,
                        "connected_at": info.connected_at.isoformat(),
                        "last_ping": info.last_ping.isoformat() if info.last_ping else None,
                        "user_agent": info.user_agent
                    }
                    for info in all_connections.values()
                ]
            },
            "notification_service": {
                "is_running": service_stats["is_running"],
                "notifications_sent": service_stats["notifications_sent"],
                "notification_interval": service_stats["notification_interval"]
            },
            "shutdown": shutdown_info,
            "configuration": {
                "host": settings.host,
                "port": settings.port,
                "workers": settings.workers,
                "debug": settings.debug,
                "log_level": settings.log_level
            }
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=status_info
        )

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        ) from e
