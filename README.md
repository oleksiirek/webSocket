# WebSocket Notification Server

A production-ready WebSocket notification server built with FastAPI that provides real-time communication capabilities with graceful shutdown mechanisms.

## Features

- **Real-time WebSocket Communication**: Bidirectional WebSocket connections with automatic client management
- **Periodic Notifications**: Configurable periodic test notifications sent to all connected clients
- **On-demand Broadcasting**: HTTP API for sending custom notifications to all clients
- **Graceful Shutdown**: Intelligent shutdown handling with connection monitoring and timeout management
- **Multi-worker Support**: Designed to work with multiple uvicorn workers for horizontal scaling
- **Production Ready**: Comprehensive logging, error handling, health checks, and monitoring
- **Docker Support**: Complete containerization with development and production configurations
- **Monitoring Integration**: Built-in Prometheus metrics and health check endpoints

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd webSocket
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the server**:
   ```bash
   python main.py
   ```

The server will start on `http://localhost:8000` by default.

## Usage

### Starting the Server

#### Development Mode
```bash
python main.py --dev
```
- Enables auto-reload on code changes
- Debug logging enabled
- Single worker process
- API documentation available at `/docs`

#### Production Mode
```bash
python main.py --prod
```
- Optimized for production
- Multiple workers (configurable)
- JSON structured logging
- Enhanced security headers

#### Custom Configuration
```bash
python main.py --host 0.0.0.0 --port 8080 --workers 4 --log-level INFO
```

### WebSocket Connection

Connect to the WebSocket endpoint at `/ws`:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function(event) {
    console.log('Connected to WebSocket server');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed');
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

### HTTP API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Send Custom Notification
```bash
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, WebSocket clients!",
    "type": "alert",
    "data": {"priority": "high"}
  }'
```

#### Get Server Metrics (JSON)
```bash
curl http://localhost:8000/metrics
```

#### Get Prometheus Metrics
```bash
curl http://localhost:8000/metrics/prometheus
```

#### Get Detailed Status
```bash
curl http://localhost:8000/status
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

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

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `WORKERS` | `1` | Number of uvicorn workers |
| `MAX_CONNECTIONS` | `1000` | Maximum concurrent WebSocket connections |
| `NOTIFICATION_INTERVAL` | `10` | Seconds between periodic notifications |
| `SHUTDOWN_TIMEOUT` | `1800` | Graceful shutdown timeout (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level (TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | `json` | Log format (json or text) |

## Docker Deployment

### Quick Start with Docker

1. **Build the image**:
   ```bash
   docker build -t websocket-notification-server .
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

### Development with Docker

```bash
# Run development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use the Makefile
make docker-dev
```

### Production Deployment

```bash
# Run production environment with monitoring
docker-compose --profile production --profile monitoring up -d

# Or use the Makefile
make docker-prod
```

## WebSocket Testing

### Using wscat (Node.js)

1. **Install wscat**:
   ```bash
   npm install -g wscat
   ```

2. **Connect to server**:
   ```bash
   wscat -c ws://localhost:8000/ws
   ```

3. **Send messages**:
   ```json
   {"type": "ping"}
   {"type": "status_request"}
   ```

### Using Python WebSocket Client

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Send ping
        await websocket.send(json.dumps({"type": "ping"}))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

# Run the test
asyncio.run(test_websocket())
```

## Graceful Shutdown

The server implements intelligent graceful shutdown:

1. **Signal Handling**: Responds to SIGTERM and SIGINT signals
2. **Connection Monitoring**: Waits for active WebSocket connections to close naturally
3. **Timeout Protection**: Forces shutdown after 30 minutes (configurable)
4. **Multi-worker Coordination**: Handles shutdown across multiple worker processes
5. **Client Notification**: Sends shutdown notifications to connected clients

### Shutdown Process

1. Stop accepting new connections
2. Stop periodic notification service
3. Send shutdown notification to all connected clients
4. Wait for connections to close naturally (up to timeout)
5. Force close remaining connections
6. Clean up resources and exit

## Monitoring and Observability

### Health Checks

The server provides comprehensive health monitoring:

- **Health Endpoint**: `/health` - Basic health status
- **Metrics Endpoint**: `/metrics` - Detailed JSON metrics
- **Prometheus Metrics**: `/metrics/prometheus` - Prometheus format
- **Status Endpoint**: `/status` - Comprehensive server status

### Logging

Structured logging with Loguru:

- **JSON Format**: Production-ready structured logs
- **Log Rotation**: Automatic log file rotation (100 MB default)
- **Log Retention**: Configurable retention period (30 days default)
- **Contextual Logging**: Automatic client ID and correlation tracking
- **Error Tracking**: Dedicated error logs with full stack traces

### Metrics

Key metrics available:

- Active WebSocket connections
- Total connections since startup
- Messages sent/received
- Server uptime
- Error rates
- Connection duration statistics

## Development

### Setting up Development Environment

1. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Run tests**:
   ```bash
   pytest tests/ -v --cov=websocket_server
   ```

4. **Code formatting**:
   ```bash
   black websocket_server/ tests/
   ruff --fix websocket_server/ tests/
   ```

### Using Makefile

Common development tasks:

```bash
make help          # Show available commands
make install       # Install dependencies
make dev           # Run development server
make test          # Run tests with coverage
make lint          # Run linting
make format        # Format code
make docker-build  # Build Docker image
make docker-dev    # Run development with Docker
```

## Architecture

### Components

- **FastAPI Application**: Main web framework with WebSocket support
- **Connection Manager**: Thread-safe WebSocket connection management
- **Notification Service**: Periodic and on-demand message broadcasting
- **Shutdown Handler**: Graceful shutdown with connection monitoring
- **Error Handler**: Comprehensive error handling and logging
- **Multi-worker Coordinator**: Coordination across uvicorn workers

### Design Patterns

- **Dependency Injection**: FastAPI's dependency system for service management
- **Singleton Pattern**: Connection manager for centralized state
- **Observer Pattern**: Signal handling for graceful shutdown
- **Service Layer**: Separation of business logic from web framework

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Check if server is running: `curl http://localhost:8000/health`
   - Verify port is not in use: `netstat -tulpn | grep 8000`

2. **WebSocket Connection Fails**:
   - Check firewall settings
   - Verify WebSocket endpoint: `wscat -c ws://localhost:8000/ws`

3. **High Memory Usage**:
   - Monitor connection count: `curl http://localhost:8000/metrics`
   - Check for connection leaks in logs

4. **Graceful Shutdown Not Working**:
   - Check signal handling in logs
   - Verify shutdown timeout configuration
   - Monitor active connections during shutdown

### Debug Mode

Enable debug mode for detailed logging:

```bash
python main.py --dev --log-level DEBUG
```

### Log Analysis

Logs are stored in the `logs/` directory:

- `websocket_server.log`: Main application logs
- `errors.log`: Error-only logs

Use `jq` for JSON log analysis:

```bash
tail -f logs/websocket_server.log | jq .
```

## Performance Considerations

### Scaling

- **Horizontal Scaling**: Use multiple uvicorn workers
- **Load Balancing**: Deploy behind nginx or similar reverse proxy
- **Connection Limits**: Configure `MAX_CONNECTIONS` based on server capacity

### Optimization

- **Memory Usage**: Monitor connection count and message throughput
- **CPU Usage**: Adjust worker count based on server cores
- **Network**: Use compression for large messages (implement as needed)

## Security

### Best Practices

- **Rate Limiting**: Implemented in nginx configuration
- **Input Validation**: All inputs validated with Pydantic models
- **Error Handling**: Sanitized error messages in production
- **Logging**: No sensitive data in logs
- **Container Security**: Non-root user in Docker containers

### Production Deployment

- Use HTTPS/WSS in production
- Implement authentication as needed
- Configure firewall rules
- Regular security updates
- Monitor for suspicious activity

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]