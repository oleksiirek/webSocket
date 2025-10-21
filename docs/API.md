# WebSocket Notification Server API Documentation

This document provides comprehensive API documentation for the WebSocket Notification Server, including all HTTP endpoints, WebSocket message formats, and usage examples.

## Table of Contents

- [HTTP API Endpoints](#http-api-endpoints)
- [WebSocket API](#websocket-api)
- [Message Formats](#message-formats)
- [Error Handling](#error-handling)
- [Examples](#examples)

## HTTP API Endpoints

### Health Check

Check the server health status and basic information.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "message": "WebSocket Notification Server is running",
  "timestamp": "2023-12-01T12:00:00.000Z",
  "connections": {
    "active": 42,
    "total": 156,
    "max_allowed": 1000
  },
  "server_info": {
    "version": "0.1.0",
    "workers": 2,
    "notification_interval": 10
  }
}
```

**Status Codes**:
- `200 OK`: Server is healthy
- `503 Service Unavailable`: Server is shutting down or unhealthy

**Example**:
```bash
curl -X GET http://localhost:8000/health
```

---

### Send Notification

Broadcast a custom notification to all connected WebSocket clients.

**Endpoint**: `POST /notify`

**Request Body**:
```json
{
  "message": "Your notification message",
  "type": "alert",
  "data": {
    "priority": "high",
    "category": "system"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Notification sent successfully",
  "recipients": 42,
  "notification": {
    "message": "Your notification message",
    "type": "alert",
    "data": {
      "priority": "high",
      "category": "system"
    }
  },
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

**Status Codes**:
- `200 OK`: Notification sent successfully
- `400 Bad Request`: Invalid request data
- `503 Service Unavailable`: Server is shutting down

**Example**:
```bash
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "System maintenance in 5 minutes",
    "type": "maintenance",
    "data": {"priority": "high"}
  }'
```

---

### Server Metrics

Get detailed server metrics and statistics.

**Endpoint**: `GET /metrics`

**Response**:
```json
{
  "connections": {
    "active_connections": 42,
    "total_connections": 156,
    "messages_sent": 1024,
    "uptime_seconds": 3600.5
  },
  "notification_service": {
    "is_running": true,
    "notification_interval": 10,
    "start_time": "2023-12-01T11:00:00.000Z"
  },
  "server": {
    "version": "0.1.0",
    "workers": 2,
    "max_connections": 1000,
    "debug_mode": false
  },
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/metrics
```

---

### Prometheus Metrics

Get metrics in Prometheus format for monitoring systems.

**Endpoint**: `GET /metrics/prometheus`

**Response** (Plain Text):
```
# HELP websocket_active_connections Number of active WebSocket connections
# TYPE websocket_active_connections gauge
websocket_active_connections 42

# HELP websocket_total_connections Total number of connections since server start
# TYPE websocket_total_connections counter
websocket_total_connections 156

# HELP websocket_notifications_sent Total number of notifications sent
# TYPE websocket_notifications_sent counter
websocket_notifications_sent 1024

# HELP websocket_server_uptime_seconds Server uptime in seconds
# TYPE websocket_server_uptime_seconds gauge
websocket_server_uptime_seconds 3600.5
```

**Example**:
```bash
curl -X GET http://localhost:8000/metrics/prometheus
```

---

### Detailed Status

Get comprehensive server status including connection details.

**Endpoint**: `GET /status`

**Response**:
```json
{
  "server": {
    "status": "running",
    "version": "0.1.0",
    "uptime_seconds": 3600.5,
    "start_time": "2023-12-01T11:00:00.000Z",
    "current_time": "2023-12-01T12:00:00.000Z"
  },
  "connections": {
    "active": 2,
    "total": 156,
    "max_allowed": 1000,
    "details": [
      {
        "client_id": "client_abc123",
        "connected_at": "2023-12-01T11:30:00.000Z",
        "last_ping": "2023-12-01T11:59:30.000Z",
        "user_agent": "Mozilla/5.0 (compatible; WebSocket client)"
      }
    ]
  },
  "notification_service": {
    "is_running": true,
    "notifications_sent": 360,
    "notification_interval": 10
  },
  "shutdown": {
    "shutdown_requested": false,
    "shutdown_timeout": 1800
  },
  "configuration": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 2,
    "debug": false,
    "log_level": "INFO"
  }
}
```

**Example**:
```bash
curl -X GET http://localhost:8000/status
```

## WebSocket API

### Connection

Connect to the WebSocket endpoint to receive real-time notifications.

**Endpoint**: `ws://localhost:8000/ws`

**Query Parameters**:
- `client_id` (optional): Custom client identifier

**Connection URL Examples**:
```
ws://localhost:8000/ws
ws://localhost:8000/ws?client_id=my_client_123
```

### Connection Lifecycle

1. **Connection Established**: Server sends welcome message
2. **Periodic Notifications**: Server sends test notifications every 10 seconds
3. **Client Messages**: Client can send ping, status requests, etc.
4. **Disconnection**: Clean disconnection or timeout handling

## Message Formats

### Server-to-Client Messages

#### Welcome Message
Sent immediately after connection is established.

```json
{
  "type": "welcome",
  "message": "Connected to WebSocket Notification Server",
  "client_id": "client_abc123",
  "server_time": "2023-12-01T12:00:00.000Z",
  "notification_interval": 10
}
```

#### Test Notification
Periodic test notifications sent every 10 seconds.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "test_notification",
  "timestamp": "2023-12-01T12:00:00.000Z",
  "data": {
    "message": "Test notification #42",
    "counter": 42,
    "uptime_seconds": 3600.5,
    "active_connections": 5,
    "server_time": "2023-12-01T12:00:00.000Z"
  },
  "sender": "notification_service"
}
```

#### Custom Notification
Notifications sent via the `/notify` API endpoint.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "type": "alert",
  "timestamp": "2023-12-01T12:00:00.000Z",
  "data": {
    "message": "System maintenance in 5 minutes",
    "priority": "high",
    "category": "maintenance"
  },
  "sender": "notification_service"
}
```

#### System Notification
System-level notifications (e.g., shutdown warnings).

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "type": "system",
  "timestamp": "2023-12-01T12:00:00.000Z",
  "data": {
    "message": "Server is shutting down. Please reconnect later.",
    "priority": "high",
    "system_time": "2023-12-01T12:00:00.000Z"
  },
  "sender": "system"
}
```

#### Ping Message
Server-initiated ping for connection health checking.

```json
{
  "type": "ping",
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

#### Pong Response
Server response to client ping.

```json
{
  "type": "pong",
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

#### Status Response
Response to client status request.

```json
{
  "type": "status_response",
  "data": {
    "active_connections": 5,
    "total_connections": 156,
    "server_time": "2023-12-01T12:00:00.000Z"
  },
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

#### Error Message
Error notifications sent to clients.

```json
{
  "type": "error",
  "error_id": "error_abc123",
  "message": "Invalid message format",
  "code": 1008,
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

#### Shutdown Notification
Sent when server is shutting down.

```json
{
  "type": "shutdown",
  "message": "Server is shutting down",
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

### Client-to-Server Messages

#### Ping Message
Client-initiated ping for connection testing.

```json
{
  "type": "ping"
}
```

#### Pong Response
Client response to server ping.

```json
{
  "type": "pong"
}
```

#### Status Request
Request current server status.

```json
{
  "type": "status_request"
}
```

## Error Handling

### HTTP Error Responses

All HTTP errors follow this format:

```json
{
  "error": {
    "id": "error_550e8400",
    "message": "Error description",
    "category": "validation",
    "timestamp": "2023-12-01T12:00:00.000Z"
  }
}
```

**Error Categories**:
- `validation`: Invalid request data
- `application`: Application logic errors
- `system`: System-level errors
- `connection`: Connection-related errors

### WebSocket Error Handling

#### Connection Errors

**Connection Limit Exceeded**:
- Close Code: `1008`
- Reason: "Connection limit exceeded: 1000/1000"

**Duplicate Connection**:
- Close Code: `1008`
- Reason: "Client client_123 is already connected"

**Server Shutting Down**:
- Close Code: `1001`
- Reason: "Server shutting down"

#### Message Errors

**Invalid JSON**:
```json
{
  "type": "error",
  "message": "Invalid JSON format",
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

**Unknown Message Type**:
```json
{
  "type": "error",
  "message": "Unknown message type: invalid_type",
  "timestamp": "2023-12-01T12:00:00.000Z"
}
```

## Examples

### JavaScript WebSocket Client

```javascript
class WebSocketClient {
  constructor(url, clientId = null) {
    this.url = clientId ? `${url}?client_id=${clientId}` : url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = (event) => {
      console.log('Connected to WebSocket server');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onclose = (event) => {
      console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
      this.handleReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'welcome':
        console.log(`Welcome! Client ID: ${data.client_id}`);
        break;
      case 'test_notification':
        console.log(`Test notification #${data.data.counter}`);
        break;
      case 'ping':
        this.sendPong();
        break;
      case 'error':
        console.error(`Server error: ${data.message}`);
        break;
      default:
        console.log('Received:', data);
    }
  }

  sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }));
    }
  }

  sendPong() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'pong' }));
    }
  }

  requestStatus() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'status_request' }));
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const client = new WebSocketClient('ws://localhost:8000/ws', 'my_client_123');
client.connect();

// Send ping every 30 seconds
setInterval(() => client.sendPing(), 30000);
```

### Python WebSocket Client

```python
import asyncio
import json
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

class WebSocketClient:
    def __init__(self, url, client_id=None):
        self.url = f"{url}?client_id={client_id}" if client_id else url
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            print(f"Connected to {self.url}")
            
            # Start listening for messages
            await self.listen()
            
        except Exception as e:
            print(f"Connection failed: {e}")

    async def listen(self):
        """Listen for messages from the server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except ConnectionClosed:
            print("Connection closed by server")
        except WebSocketException as e:
            print(f"WebSocket error: {e}")
        finally:
            self.running = False

    async def handle_message(self, data):
        """Handle incoming messages."""
        message_type = data.get('type', 'unknown')
        
        if message_type == 'welcome':
            print(f"Welcome! Client ID: {data.get('client_id')}")
        elif message_type == 'test_notification':
            counter = data.get('data', {}).get('counter', 0)
            print(f"Test notification #{counter}")
        elif message_type == 'ping':
            await self.send_pong()
        elif message_type == 'error':
            print(f"Server error: {data.get('message')}")
        else:
            print(f"Received {message_type}: {data}")

    async def send_message(self, message):
        """Send a message to the server."""
        if self.websocket and self.running:
            await self.websocket.send(json.dumps(message))

    async def send_ping(self):
        """Send a ping message."""
        await self.send_message({"type": "ping"})

    async def send_pong(self):
        """Send a pong response."""
        await self.send_message({"type": "pong"})

    async def request_status(self):
        """Request server status."""
        await self.send_message({"type": "status_request"})

    async def disconnect(self):
        """Disconnect from the server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()

# Usage example
async def main():
    client = WebSocketClient('ws://localhost:8000/ws', 'python_client_123')
    
    # Connect and run
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("Disconnecting...")
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### HTTP API Client Examples

#### Python HTTP Client

```python
import requests
import json

class NotificationClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def check_health(self):
        """Check server health."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def send_notification(self, message, notification_type="custom", data=None):
        """Send a custom notification."""
        payload = {
            "message": message,
            "type": notification_type,
            "data": data or {}
        }
        response = requests.post(
            f"{self.base_url}/notify",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return response.json()

    def get_metrics(self):
        """Get server metrics."""
        response = requests.get(f"{self.base_url}/metrics")
        return response.json()

    def get_status(self):
        """Get detailed server status."""
        response = requests.get(f"{self.base_url}/status")
        return response.json()

# Usage
client = NotificationClient()

# Check health
health = client.check_health()
print(f"Server status: {health['status']}")

# Send notification
result = client.send_notification(
    "Hello from Python!",
    "alert",
    {"priority": "normal"}
)
print(f"Notification sent to {result['recipients']} clients")

# Get metrics
metrics = client.get_metrics()
print(f"Active connections: {metrics['connections']['active_connections']}")
```

#### cURL Examples

```bash
# Health check
curl -X GET http://localhost:8000/health | jq .

# Send notification
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "System maintenance starting",
    "type": "maintenance",
    "data": {"duration": "30 minutes", "priority": "high"}
  }' | jq .

# Get metrics
curl -X GET http://localhost:8000/metrics | jq .

# Get Prometheus metrics
curl -X GET http://localhost:8000/metrics/prometheus

# Get detailed status
curl -X GET http://localhost:8000/status | jq .
```

## Rate Limiting

When deployed behind nginx (as in the provided configuration), the following rate limits apply:

- **WebSocket connections**: 5 requests per second per IP
- **API endpoints**: 10 requests per second per IP
- **Burst allowance**: 10-20 requests depending on endpoint

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Requests per time window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

## Authentication

The current implementation does not include authentication. For production use, consider implementing:

1. **API Key Authentication**: Add API key validation for HTTP endpoints
2. **JWT Tokens**: Use JWT tokens for WebSocket authentication
3. **OAuth 2.0**: Integrate with OAuth providers
4. **Custom Authentication**: Implement domain-specific authentication

Example authentication middleware can be added to the FastAPI application as needed.