"""Application configuration and settings."""


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server bind address"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port number"
    )
    workers: int = Field(
        default=1,
        ge=1,
        le=32,
        description="Number of uvicorn worker processes"
    )

    # WebSocket Configuration
    ping_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="WebSocket ping interval in seconds"
    )
    ping_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="WebSocket ping timeout in seconds"
    )
    max_connections: int = Field(
        default=1000,
        ge=1,
        le=100000,
        description="Maximum number of concurrent WebSocket connections"
    )

    # Notification Configuration
    notification_interval: int = Field(
        default=10,
        ge=1,
        le=3600,
        description="Interval between periodic notifications in seconds"
    )

    # Shutdown Configuration
    shutdown_timeout: int = Field(
        default=1800,  # 30 minutes
        ge=60,
        le=7200,
        description="Graceful shutdown timeout in seconds"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    log_rotation: str = Field(
        default="100 MB",
        description="Log file rotation size"
    )
    log_retention: str = Field(
        default="30 days",
        description="Log file retention period"
    )

    # Development Settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development"
    )

    # Monitoring Settings
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics endpoint"
    )
    health_check_enabled: bool = Field(
        default=True,
        description="Enable health check endpoint"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is supported by Loguru."""
        valid_levels = {
            "TRACE", "DEBUG", "INFO", "SUCCESS",
            "WARNING", "ERROR", "CRITICAL"
        }
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v_upper

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is supported."""
        valid_formats = {"json", "text"}
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(
                f"Invalid log format '{v}'. Must be one of: {', '.join(valid_formats)}"
            )
        return v_lower

    @field_validator("ping_timeout")
    @classmethod
    def validate_ping_timeout(cls, v: int, info) -> int:
        """Ensure ping timeout is less than ping interval."""
        ping_interval = info.data.get("ping_interval", 30) if info.data else 30
        if v >= ping_interval:
            raise ValueError(
                f"ping_timeout ({v}) must be less than ping_interval ({ping_interval})"
            )
        return v

    def get_uvicorn_config(self) -> dict:
        """Get configuration dictionary for uvicorn server."""
        return {
            "host": self.host,
            "port": self.port,
            "workers": self.workers if not self.debug else 1,
            "reload": self.reload and self.debug,
            "log_level": self.log_level.lower(),
            "access_log": self.debug,
        }

    def get_loguru_config(self) -> dict:
        """Get configuration dictionary for Loguru logging."""
        config = {
            "level": self.log_level,
            "rotation": self.log_rotation,
            "retention": self.log_retention,
            "compression": "gz",
            "backtrace": self.debug,
            "diagnose": self.debug,
        }

        if self.log_format == "json":
            config["serialize"] = True

        return config


# Global settings instance
settings = Settings()
