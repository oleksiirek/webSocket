# WebSocket Notification Server - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

### Running the Server

#### Development Mode (Recommended for testing)
```bash
python main.py --dev
```
- ✅ Auto-reload on code changes
- ✅ Debug logging enabled  
- ✅ API documentation at http://localhost:8000/docs
- ✅ Clean, readable console logs

#### Production Mode
```bash
python main.py --prod
```
- ✅ Optimized for production
- ✅ JSON structured logging
- ✅ Multiple workers support

#### Default Mode
```bash
python main.py
```

### Available Endpoints

Once the server is running on `http://localhost:8000`:

| Endpoint | Type | Description |
|----------|------|-------------|
| `/ws` | WebSocket | Main WebSocket connection endpoint |
| `/health` | GET | Health check and server status |
| `/notify` | POST | Send custom notifications to all clients |
| `/metrics` | GET | Server metrics and statistics (JSON format) |
| `/metrics/prometheus` | GET | Prometheus-compatible metrics |
| `/status` | GET | Detailed server status |
| `/docs` | GET | API documentation (dev mode only) |

## 🧪 Testing the Server

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### Run Comprehensive Tests
```bash
python test_server.py
```

### WebSocket Client Example
```bash
# Listen for messages
python example_client.py

# Interactive mode
python example_client.py --interactive
```

### Send Custom Notification
```bash
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello WebSocket clients!",
    "type": "alert",
    "data": {"priority": "high"}
  }'
```

### Check Prometheus Metrics
```bash
curl http://localhost:8000/metrics/prometheus
```

## 📋 What You Should See

### Server Startup (Development Mode)
```
============================================================
WebSocket Notification Server
============================================================
Version: 0.1.0
Host: 0.0.0.0
Port: 8000
Workers: 1
Debug Mode: True
Log Level: INFO

Available Endpoints:
  WebSocket: ws://0.0.0.0:8000/ws
  Health Check: http://0.0.0.0:8000/health
  Notifications: http://0.0.0.0:8000/notify
  Metrics: http://0.0.0.0:8000/metrics
  Status: http://0.0.0.0:8000/status
  API Docs: http://0.0.0.0:8000/docs
  ReDoc: http://0.0.0.0:8000/redoc
============================================================

2025-10-21 21:35:48.487 | INFO | Starting WebSocket Notification Server
2025-10-21 21:35:48.493 | INFO | Started periodic notifications (interval: 10s)
2025-10-21 21:35:48.495 | INFO | WebSocket Notification Server started successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Successful Test Results
```
🚀 Starting WebSocket Notification Server Tests
==================================================
✅ PASS - Health Check
✅ PASS - WebSocket Connection  
✅ PASS - Notification Endpoint
✅ PASS - Metrics Endpoint

🎯 Tests passed: 4/4
🎉 All tests passed! Server is working correctly.
```

## 🔧 Configuration

### Environment Variables (.env file)
```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# WebSocket Configuration  
MAX_CONNECTIONS=1000
PING_INTERVAL=30
PING_TIMEOUT=10

# Notification Configuration
NOTIFICATION_INTERVAL=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=text  # Use 'json' for production
DEBUG=true       # Set to 'false' for production
```

### Command Line Options
```bash
python main.py --help

# Examples:
python main.py --host 0.0.0.0 --port 8080
python main.py --workers 4 --log-level DEBUG
```

## 🌟 Key Features Working

✅ **Real-time WebSocket Communication** - Bidirectional messaging  
✅ **Periodic Notifications** - Automatic test messages every 10 seconds  
✅ **HTTP API** - REST endpoints for health, metrics, and notifications  
✅ **Graceful Shutdown** - Clean connection handling on server stop  
✅ **Auto-reload Development** - Code changes trigger server restart  
✅ **Comprehensive Logging** - Structured, readable logs  
✅ **Error Handling** - Robust error management and recovery  
✅ **Client Management** - Automatic connection tracking and cleanup  

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill existing processes on port 8000
lsof -ti:8000 | xargs kill -9
```

### Connection Issues
- Verify server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Ensure WebSocket client connects to correct URL

### Debug Mode
```bash
python main.py --dev --log-level DEBUG
```

## 📚 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Build a client**: Use `example_client.py` as a starting point
3. **Customize notifications**: Modify the notification service
4. **Add authentication**: Implement user authentication as needed
5. **Scale up**: Use multiple workers for production deployment

## 🎯 Production Deployment

For production use:
1. Set `DEBUG=false` and `LOG_FORMAT=json` in `.env`
2. Use `python main.py --prod` 
3. Configure reverse proxy (nginx)
4. Set up monitoring and logging
5. Use multiple workers: `--workers 4`

---

**🎉 Congratulations! Your WebSocket Notification Server is ready to use!**