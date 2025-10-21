# Configuration Reference

This document provides a comprehensive reference for all configuration options available in the WebSocket Notification Server.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Configuration File](#configuration-file)
- [Command Line Arguments](#command-line-arguments)
- [Docker Configuration](#docker-configuration)
- [Production Settings](#production-settings)
- [Development Settings](#development-settings)

## Environment Variables

Configuration is primarily managed through environment variables. Create a `.env` file in the project root or set these variables in your deployment environment.

### Server Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HOST` | string | `0.0.0.0` | Server bind address. Use `127.0.0.1` for localhost only |
| `PORT` | integer | `8000` | Server port number (1-65535) |
| `WORKERS` | integer | `1` | Number of uvicorn worker processes (1-32) |

**Examples**:
```bash
HOST=0.0.0.0          # Bind to all interfaces
HOST=127.0.0.1        # Localhost only
PORT=8080             # Custom port
WORKERS=4             # 4 worker processes
```

### WebSocket Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PING_INTERVAL` | integer | `30` | WebSocket ping interval in seconds (5-300) |
| `PING_TIMEOUT` | integer | `10` | WebSocket ping timeout in seconds (1-60) |
| `MAX_CONNECTIONS` | integer | `1000` | Maximum concurrent WebSocket connections (1-100000) |

**Examples**:
```bash
PING_INTERVAL=60      # Ping every 60 seconds
PING_TIMEOUT=15       # 15 second ping timeout
MAX_CONNECTIONS=5000  # Allow up to 5000 connections
```

**Important**: `PING_TIMEOUT` must be less than `PING_INTERVAL`.

### Notification Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NOTIFICATION_INTERVAL` | integer | `10` | Interval between periodic notifications in seconds (1-3600) |

**Examples**:
```bash
NOTIFICATION_INTERVAL=5   # Send notifications every 5 seconds
NOTIFICATION_INTERVAL=30  # Send notifications every 30 seconds
```

### Shutdown Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SHUTDOWN_TIMEOUT` | integer | `1800` | Graceful shutdown timeout in seconds (60-7200) |

**Examples**:
```bash
SHUTDOWN_TIMEOUT=600   # 10 minute timeout
SHUTDOWN_TIMEOUT=3600  # 1 hour timeout
```

### Logging Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `LOG_FORMAT` | string | `json` | Log output format |
| `LOG_ROTATION` | string | `100 MB` | Log file rotation size |
| `LOG_RETENTION` | string | `30 days` | Log file retention period |

**Log Levels** (in order of verbosity):
- `TRACE`: Most verbose, includes all debug information
- `DEBUG`: Debug information for development
- `INFO`: General information messages
- `SUCCESS`: Success operation messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors that may cause shutdown

**Log Formats**:
- `json`: Structured JSON format (recommended for production)
- `text`: Human-readable text format (recommended for development)

**Examples**:
```bash
LOG_LEVEL=DEBUG           # Enable debug logging
LOG_FORMAT=text           # Human-readable logs
LOG_ROTATION="50 MB"      # Rotate at 50MB
LOG_RETENTION="7 days"    # Keep logs for 7 days
```

### Development Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEBUG` | boolean | `false` | Enable debug mode |
| `RELOAD` | boolean | `false` | Enable auto-reload for development |

**Examples**:
```bash
DEBUG=true     # Enable debug mode
RELOAD=true    # Enable auto-reload
```

### Monitoring Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `METRICS_ENABLED` | boolean | `true` | Enable Prometheus metrics endpoint |
| `HEALTH_CHECK_ENABLED` | boolean | `true` | Enable health check endpoint |

**Examples**:
```bash
METRICS_ENABLED=false        # Disable metrics
HEALTH_CHECK_ENABLED=false   # Disable health checks
```

## Configuration File

### .env File Format

Create a `.env` file in the project root:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=2

# WebSocket Configuration
PING_INTERVAL=30
PING_TIMEOUT=10
MAX_CONNECTIONS=1000

# Notification Configuration
NOTIFICATION_INTERVAL=10

# Shutdown Configuration
SHUTDOWN_TIMEOUT=1800

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ROTATION=100 MB
LOG_RETENTION=30 days

# Development Settings
DEBUG=false
RELOAD=false

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### Environment-Specific Configurations

#### Development (.env.dev)
```bash
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
WORKERS=1
MAX_CONNECTIONS=100
```

#### Production (.env.prod)
```bash
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
LOG_FORMAT=json
WORKERS=4
MAX_CONNECTIONS=5000
SHUTDOWN_TIMEOUT=3600
```

#### Testing (.env.test)
```bash
DEBUG=true
LOG_LEVEL=WARNING
WORKERS=1
MAX_CONNECTIONS=10
NOTIFICATION_INTERVAL=1
```

## Command Line Arguments

Override configuration using command line arguments:

```bash
python main.py [OPTIONS]
```

### Available Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--dev` | flag | Run in development mode |
| `--prod` | flag | Run in production mode |
| `--host HOST` | string | Override host setting |
| `--port PORT` | integer | Override port setting |
| `--workers N` | integer | Override worker count |
| `--log-level LEVEL` | string | Override log level |
| `--check-deps` | flag | Check dependencies and exit |
| `--info` | flag | Show server info and exit |

### Examples

```bash
# Development mode
python main.py --dev

# Production mode
python main.py --prod

# Custom host and port
python main.py --host 127.0.0.1 --port 8080

# Multiple workers with debug logging
python main.py --workers 4 --log-level DEBUG

# Check dependencies
python main.py --check-deps

# Show server information
python main.py --info
```

## Docker Configuration

### Environment Variables in Docker

#### docker-compose.yml
```yaml
services:
  websocket-server:
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - WORKERS=2
      - LOG_LEVEL=INFO
      - MAX_CONNECTIONS=1000
```

#### Docker Run
```bash
docker run -e HOST=0.0.0.0 -e PORT=8000 -e WORKERS=2 webSocket```

#### .env File with Docker
```bash
# Use .env file with docker-compose
docker-compose --env-file .env.prod up
```

### Docker Build Arguments

```dockerfile
# Dockerfile with build arguments
ARG LOG_LEVEL=INFO
ARG MAX_CONNECTIONS=1000
ENV LOG_LEVEL=${LOG_LEVEL}
ENV MAX_CONNECTIONS=${MAX_CONNECTIONS}
```

```bash
# Build with custom arguments
docker build --build-arg LOG_LEVEL=DEBUG --build-arg MAX_CONNECTIONS=500 .
```

## Production Settings

### Recommended Production Configuration

```bash
# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4                    # Adjust based on CPU cores

# WebSocket
PING_INTERVAL=30
PING_TIMEOUT=10
MAX_CONNECTIONS=5000         # Adjust based on server capacity

# Notifications
NOTIFICATION_INTERVAL=10

# Shutdown
SHUTDOWN_TIMEOUT=3600        # 1 hour for graceful shutdown

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ROTATION=100 MB
LOG_RETENTION=30 days

# Security
DEBUG=false
RELOAD=false

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### Performance Tuning

#### High-Traffic Configuration
```bash
# For high-traffic scenarios
WORKERS=8                    # More workers
MAX_CONNECTIONS=10000        # Higher connection limit
PING_INTERVAL=60             # Less frequent pings
NOTIFICATION_INTERVAL=30     # Less frequent notifications
LOG_LEVEL=WARNING            # Reduce log verbosity
```

#### Resource-Constrained Configuration
```bash
# For limited resources
WORKERS=1                    # Single worker
MAX_CONNECTIONS=100          # Lower connection limit
PING_INTERVAL=120            # Less frequent pings
LOG_ROTATION=10 MB           # Smaller log files
LOG_RETENTION=7 days         # Shorter retention
```

### Security Configuration

```bash
# Security-focused settings
DEBUG=false                  # Never enable in production
LOG_LEVEL=WARNING            # Reduce information disclosure
METRICS_ENABLED=false        # Disable if not needed
```

## Development Settings

### Recommended Development Configuration

```bash
# Server
HOST=127.0.0.1              # Localhost only
PORT=8000
WORKERS=1                    # Single worker for debugging

# WebSocket
MAX_CONNECTIONS=10           # Lower limit for testing

# Notifications
NOTIFICATION_INTERVAL=5      # Faster notifications for testing

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text              # Human-readable logs
LOG_ROTATION=10 MB           # Smaller files
LOG_RETENTION=3 days         # Shorter retention

# Development
DEBUG=true
RELOAD=true                  # Auto-reload on changes

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

### Testing Configuration

```bash
# For automated testing
LOG_LEVEL=ERROR              # Minimal logging
WORKERS=1                    # Single worker
MAX_CONNECTIONS=5            # Very low limit
NOTIFICATION_INTERVAL=1      # Fast notifications
SHUTDOWN_TIMEOUT=60          # Quick shutdown
```

## Configuration Validation

The server validates all configuration values on startup:

### Validation Rules

1. **Port Range**: 1-65535
2. **Worker Count**: 1-32
3. **Ping Timeout**: Must be less than ping interval
4. **Log Level**: Must be valid Loguru level
5. **Log Format**: Must be 'json' or 'text'
6. **Connection Limits**: Positive integers
7. **Time Values**: Positive integers within reasonable ranges

### Validation Errors

Invalid configurations will cause startup failure with descriptive error messages:

```
ValueError: ping_timeout (30) must be less than ping_interval (30)
ValueError: Invalid log level 'INVALID'. Must be one of: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
ValueError: Invalid log format 'xml'. Must be one of: json, text
```

## Configuration Precedence

Configuration values are applied in this order (highest to lowest precedence):

1. **Command Line Arguments**: `--host`, `--port`, etc.
2. **Environment Variables**: `HOST`, `PORT`, etc.
3. **Default Values**: Built-in defaults

### Example

```bash
# .env file
PORT=8000

# Command line
python main.py --port 8080

# Result: Server runs on port 8080 (command line overrides .env)
```

## Configuration Best Practices

### Security
- Never commit `.env` files with sensitive data
- Use different configurations for different environments
- Disable debug mode in production
- Restrict metrics endpoint access

### Performance
- Adjust worker count based on CPU cores (typically CPU cores × 2)
- Set connection limits based on available memory
- Use JSON logging format in production
- Configure appropriate log rotation and retention

### Monitoring
- Enable health checks for load balancer integration
- Enable metrics for monitoring systems
- Use structured logging for log analysis
- Set appropriate log levels for each environment

### Deployment
- Use environment-specific configuration files
- Validate configuration in CI/CD pipelines
- Document configuration changes
- Test configuration changes in staging environments