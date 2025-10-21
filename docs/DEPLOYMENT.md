# Deployment Guide

This guide covers various deployment scenarios for the WebSocket Notification Server, from local development to production environments.

## Table of Contents

- [Quick Deployment](#quick-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring Setup](#monitoring-setup)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Quick Deployment

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd webSocket   cp .env.example .env
   pip install -r requirements.txt
   ```

2. **Run development server**:
   ```bash
   python main.py --dev
   ```

3. **Test connection**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # WebSocket test
   wscat -c ws://localhost:8000/ws
   ```

### Quick Production Test

```bash
# Run with production settings
python main.py --prod --workers 2

# Or with Docker
docker-compose up -d
```

## Docker Deployment

### Single Container

#### Build and Run
```bash
# Build image
docker build -t websocket-notification-server .

# Run container
docker run -d \
  --name websocket-server \
  -p 8000:8000 \
  -e WORKERS=2 \
  -e MAX_CONNECTIONS=1000 \
  -v $(pwd)/logs:/app/logs \
  webSocket
```

#### With Environment File
```bash
# Create production environment file
cat > .env.prod << EOF
HOST=0.0.0.0
PORT=8000
WORKERS=4
MAX_CONNECTIONS=5000
LOG_LEVEL=INFO
LOG_FORMAT=json
DEBUG=false
EOF

# Run with environment file
docker run -d \
  --name websocket-server \
  -p 8000:8000 \
  --env-file .env.prod \
  -v $(pwd)/logs:/app/logs \
  webSocket```

### Docker Compose

#### Basic Setup
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f websocket-server

# Stop services
docker-compose down
```

#### With Monitoring
```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access services
# - WebSocket Server: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

#### Development Mode
```bash
# Development with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or use Makefile
make docker-dev
```

### Multi-Stage Build

The provided Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Development stage
FROM python:3.11-slim as builder
# ... build dependencies

# Production stage  
FROM python:3.11-slim as production
# ... runtime only
```

Benefits:
- Smaller production images
- Faster deployment
- Better security (no build tools in production)

## Production Deployment

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Storage**: 10 GB
- **Network**: 100 Mbps

#### Recommended for High Traffic
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Storage**: 100+ GB SSD
- **Network**: 1+ Gbps

### Production Configuration

#### Environment Setup
```bash
# Create production user
sudo useradd -r -s /bin/false websocket

# Create application directory
sudo mkdir -p /opt/websocket-server
sudo chown websocket:websocket /opt/websocket-server

# Create logs directory
sudo mkdir -p /var/log/websocket-server
sudo chown websocket:websocket /var/log/websocket-server
```

#### Production Environment File
```bash
# /opt/websocket-server/.env
HOST=0.0.0.0
PORT=8000
WORKERS=8
MAX_CONNECTIONS=10000
PING_INTERVAL=60
NOTIFICATION_INTERVAL=30
SHUTDOWN_TIMEOUT=3600
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ROTATION=100 MB
LOG_RETENTION=30 days
DEBUG=false
METRICS_ENABLED=true
```

### Systemd Service

Create a systemd service for automatic startup:

```bash
# /etc/systemd/system/websocket-server.service
[Unit]
Description=WebSocket Notification Server
After=network.target
Wants=network.target

[Service]
Type=exec
User=websocket
Group=websocket
WorkingDirectory=/opt/websocket-server
Environment=PATH=/opt/websocket-server/venv/bin
ExecStart=/opt/websocket-server/venv/bin/python main.py --prod
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=1800
Restart=on-failure
RestartSec=5

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/websocket-server

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable websocket-server
sudo systemctl start websocket-server

# Check status
sudo systemctl status websocket-server
```

### Reverse Proxy Setup

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/websocket-server
upstream websocket_backend {
    server 127.0.0.1:8000;
    # Add more servers for load balancing
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=websocket:10m rate=5r/s;

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # WebSocket endpoint
    location /ws {
        limit_req zone=websocket burst=10 nodelay;
        
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
    # API endpoints
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://websocket_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check (no rate limiting)
    location /health {
        proxy_pass http://websocket_backend;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/websocket-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Apache Configuration

```apache
# /etc/apache2/sites-available/websocket-server.conf
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com
    
    # SSL configuration
    SSLEngine on
    SSLCertificateFile /path/to/your/cert.pem
    SSLCertificateKeyFile /path/to/your/key.pem
    
    # WebSocket proxy
    ProxyPreserveHost On
    ProxyRequests Off
    
    # WebSocket endpoint
    ProxyPass /ws ws://127.0.0.1:8000/ws
    ProxyPassReverse /ws ws://127.0.0.1:8000/ws
    
    # HTTP endpoints
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    
    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options DENY
    Header always set X-Content-Type-Options nosniff
</VirtualHost>
```

### Load Balancing

#### Multiple Server Instances

```bash
# Start multiple instances
python main.py --port 8000 --workers 4 &
python main.py --port 8001 --workers 4 &
python main.py --port 8002 --workers 4 &
```

#### Nginx Load Balancing

```nginx
upstream websocket_backend {
    least_conn;  # Load balancing method
    server 127.0.0.1:8000 weight=3;
    server 127.0.0.1:8001 weight=3;
    server 127.0.0.1:8002 weight=3;
    
    # Health checks (nginx plus)
    # health_check interval=30s fails=3 passes=2;
}
```

## Cloud Deployment

### AWS Deployment

#### ECS with Fargate

```yaml
# task-definition.json
{
  "family": "websocket-server",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "websocket-server",
      "image": "your-account.dkr.ecr.region.amazonaws.com/websocket-server:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "WORKERS", "value": "4"},
        {"name": "MAX_CONNECTIONS", "value": "5000"},
        {"name": "LOG_FORMAT", "value": "json"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/websocket-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Application Load Balancer

```yaml
# ALB configuration for WebSocket support
TargetGroup:
  Protocol: HTTP
  Port: 8000
  HealthCheckPath: /health
  HealthCheckProtocol: HTTP
  
Listener:
  Protocol: HTTPS
  Port: 443
  DefaultActions:
    - Type: forward
      TargetGroupArn: !Ref TargetGroup
```

### Google Cloud Platform

#### Cloud Run

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: websocket-server
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 1000
      containers:
      - image: gcr.io/project-id/websocket-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: WORKERS
          value: "4"
        - name: MAX_CONNECTIONS
          value: "5000"
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
```

```bash
# Deploy to Cloud Run
gcloud run deploy websocket-server \
  --image gcr.io/project-id/websocket-server:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10
```

### Kubernetes Deployment

#### Deployment Manifest

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: websocket-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: websocket-server
  template:
    metadata:
      labels:
        app: websocket-server
    spec:
      containers:
      - name: websocket-server
        image: websocket-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: WORKERS
          value: "4"
        - name: MAX_CONNECTIONS
          value: "5000"
        - name: LOG_FORMAT
          value: "json"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: websocket-server-service
spec:
  selector:
    app: websocket-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -l app=websocket-server
kubectl get service websocket-server-service
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'websocket-server'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 30s
```

### Grafana Dashboard

Import the provided Grafana dashboard or create custom panels:

```json
{
  "dashboard": {
    "title": "WebSocket Server Metrics",
    "panels": [
      {
        "title": "Active Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "websocket_active_connections"
          }
        ]
      },
      {
        "title": "Connection Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(websocket_total_connections[5m])"
          }
        ]
      }
    ]
  }
}
```

### Log Aggregation

#### ELK Stack

```yaml
# docker-compose.elk.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
  
  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

#### Fluentd Configuration

```ruby
# fluent.conf
<source>
  @type tail
  path /var/log/websocket-server/*.log
  pos_file /var/log/fluentd/websocket-server.log.pos
  tag websocket.server
  format json
</source>

<match websocket.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name websocket-logs
</match>
```

## Security Considerations

### Network Security

```bash
# Firewall rules (ufw)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 8000/tcp     # Block direct access to app
sudo ufw enable
```

### Application Security

1. **Environment Variables**: Never commit sensitive data
2. **User Permissions**: Run as non-root user
3. **Input Validation**: All inputs are validated
4. **Rate Limiting**: Implemented in reverse proxy
5. **HTTPS/WSS**: Use encrypted connections in production

### Container Security

```dockerfile
# Security best practices in Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set security options
USER appuser
WORKDIR /app

# Read-only filesystem (where possible)
# --read-only flag when running container
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
docker stats websocket-server

# Monitor connections
curl http://localhost:8000/metrics | jq '.connections'

# Check for memory leaks
ps aux | grep python
```

#### Connection Issues
```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Check network connectivity
netstat -tulpn | grep 8000

# Verify firewall rules
sudo ufw status
```

#### Performance Issues
```bash
# Monitor CPU usage
top -p $(pgrep -f "python main.py")

# Check worker processes
ps aux | grep uvicorn

# Monitor request rates
curl http://localhost:8000/metrics/prometheus | grep rate
```

### Log Analysis

```bash
# View recent logs
tail -f logs/websocket_server.log | jq .

# Filter error logs
grep -E '"level":"ERROR"' logs/websocket_server.log | jq .

# Monitor connection events
grep -E '"websocket"' logs/websocket_server.log | jq .
```

### Health Checks

```bash
# Basic health check
curl -f http://localhost:8000/health || echo "Server unhealthy"

# Detailed status
curl http://localhost:8000/status | jq .

# Check metrics
curl http://localhost:8000/metrics | jq '.connections'
```

### Recovery Procedures

#### Graceful Restart
```bash
# Send SIGTERM for graceful shutdown
sudo systemctl reload websocket-server

# Or with Docker
docker-compose restart websocket-server
```

#### Emergency Restart
```bash
# Force restart if graceful fails
sudo systemctl restart websocket-server

# Or with Docker
docker-compose down && docker-compose up -d
```

This deployment guide covers the most common scenarios. For specific environments or requirements, adapt the configurations accordingly.