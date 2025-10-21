"""WebSocket message models."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class NotificationMessage(BaseModel):
    """Model for WebSocket notification messages."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the message"
    )
    type: str = Field(
        default="notification",
        description="Type of message being sent"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when message was created"
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Message payload data"
    )
    sender: str = Field(
        default="server",
        description="Identifier of the message sender"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "notification",
                "timestamp": "2023-12-01T12:00:00.000Z",
                "data": {
                    "message": "Test notification",
                    "priority": "normal"
                },
                "sender": "server"
            }
        }
    )


class ConnectionInfo(BaseModel):
    """Model for tracking WebSocket connection information."""

    client_id: str = Field(
        description="Unique identifier for the client connection"
    )
    connected_at: datetime = Field(
        description="UTC timestamp when connection was established"
    )
    last_ping: datetime | None = Field(
        default=None,
        description="UTC timestamp of last ping received from client"
    )
    user_agent: str | None = Field(
        default=None,
        description="User agent string from client headers"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": "client_123",
                "connected_at": "2023-12-01T12:00:00.000Z",
                "last_ping": "2023-12-01T12:05:00.000Z",
                "user_agent": "Mozilla/5.0 (compatible; WebSocket client)"
            }
        }
    )


class BroadcastRequest(BaseModel):
    """Model for API requests to broadcast messages."""

    message: str = Field(
        description="Message content to broadcast"
    )
    type: str = Field(
        default="broadcast",
        description="Type of broadcast message"
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional data to include in broadcast"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "System maintenance in 5 minutes",
                "type": "alert",
                "data": {
                    "priority": "high",
                    "category": "maintenance"
                }
            }
        }
    )


class ConnectionStats(BaseModel):
    """Model for connection statistics."""

    active_connections: int = Field(
        description="Number of currently active connections"
    )
    total_connections: int = Field(
        description="Total connections since server start"
    )
    messages_sent: int = Field(
        description="Total messages sent since server start"
    )
    uptime_seconds: float = Field(
        description="Server uptime in seconds"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "active_connections": 42,
                "total_connections": 156,
                "messages_sent": 1024,
                "uptime_seconds": 3600.5
            }
        }
    )
