# Developer Setup Guide

## Quick Start for New Developers

### 1. Clone and Setup
```bash
git clone <your-repository-url>
cd websocket-notification-server
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### 3. Verify Installation
```bash
make test          # Run all tests
make lint          # Check code quality
python main.py --info  # Show server info
```

### 4. Start Development Server
```bash
make dev           # Start with auto-reload
# Or manually:
python main.py --dev
```

### 5. Test WebSocket Connection
```bash
# In another terminal
pip install websocket-client
python example_client.py
```

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `hotfix/*`: Critical bug fixes

### Making Changes
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make your changes
make format        # Format code
make lint          # Check linting
make test          # Run tests

git add .
git commit -m "feat(scope): description"
git push origin feature/your-feature-name
```

### Code Quality Checks
```bash
make format        # Black + Ruff formatting
make lint          # Ruff + MyPy checking
make test          # Full test suite
```

### Docker Development
```bash
make docker-build  # Build image
make docker-dev    # Run with Docker Compose
make docker-stop   # Stop containers
```

## Project Structure
```
websocket-notification-server/
├── websocket_server/          # Main application code
│   ├── config/               # Configuration management
│   ├── endpoints/            # HTTP and WebSocket endpoints
│   ├── handlers/             # Error and shutdown handlers
│   ├── models/               # Data models
│   └── services/             # Business logic services
├── tests/                    # Test suite
├── docs/                     # Additional documentation
├── main.py                   # Application entry point
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
└── docker-compose.yml        # Docker configuration
```

## Key Features Implemented
- ✅ Real-time WebSocket communication
- ✅ Periodic notification broadcasting
- ✅ On-demand HTTP notification API
- ✅ Graceful shutdown handling
- ✅ Multi-worker support
- ✅ Comprehensive logging
- ✅ Health checks and metrics
- ✅ Docker containerization
- ✅ Complete test coverage
- ✅ Production-ready configuration

## Testing
```bash
# Run all tests
make test

# Run specific test categories
pytest tests/test_connection_manager.py -v
pytest tests/test_websocket_integration.py -v
pytest -m "not slow" tests/  # Skip slow tests

# Run with coverage
pytest --cov=websocket_server --cov-report=html
```

## Debugging
```bash
# Debug mode with detailed logging
python main.py --dev --log-level DEBUG

# Check server health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics | jq .
```

## Common Issues

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill process if needed
kill -9 <PID>
```

### Dependencies Issues
```bash
# Clean and reinstall
make clean
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Docker Issues
```bash
# Clean Docker environment
make docker-clean
docker system prune -f
```

## Performance Testing
```bash
# Install load testing tools
npm install -g wscat

# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Load test HTTP endpoints
curl -X POST http://localhost:8000/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "type": "info"}'
```

## Production Deployment
```bash
# Production mode
python main.py --prod --workers 4

# With Docker
docker-compose --profile production up -d

# With monitoring
docker-compose --profile production --profile monitoring up -d
```

## Need Help?
- Check the [README.md](README.md) for detailed documentation
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Look at existing tests for examples
- Open an issue for bugs or questions