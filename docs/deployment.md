# Deployment Guide

Production deployment instructions for Agent-Core.

---

## Overview

This guide covers deploying Agent-Core to production on various platforms.

---

## Local Server

### Quick Start
```bash
# Install
pip install agent-corex uvicorn

# Run
uvicorn agent_core.api.main:app --host 0.0.0.0 --port 8000

# Test
curl http://localhost:8000/health
```

### Configuration
```bash
# With environment variables
export MCP_CONFIG=/etc/agent-corex/mcp.json
export LOG_LEVEL=info
uvicorn agent_core.api.main:app --host 0.0.0.0 --port 8000
```

---

## Docker

### Build Image
```bash
# Clone repo
git clone https://github.com/ankitpro/agent-corex.git
cd agent-corex

# Build
docker build -t agent-corex:latest .

# Run
docker run -d \
  -p 8000:8000 \
  -e MCP_CONFIG=/config/mcp.json \
  -v /path/to/config:/config \
  agent-corex:latest
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  agent-corex:
    image: agent-corex:latest
    ports:
      - "8000:8000"
    environment:
      - MCP_CONFIG=/config/mcp.json
      - LOG_LEVEL=info
    volumes:
      - ./config:/config
    restart: always
```

Run with:
```bash
docker-compose up -d
```

---

## Kubernetes

### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-corex
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-corex
  template:
    metadata:
      labels:
        app: agent-corex
    spec:
      containers:
      - name: agent-corex
        image: agent-corex:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_CONFIG
          value: /config/mcp.json
        - name: LOG_LEVEL
          value: info
        volumeMounts:
        - name: config
          mountPath: /config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: agent-corex-config
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-corex
spec:
  selector:
    app: agent-corex
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy with:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

---

## Cloud Platforms

### Heroku
```bash
# Install Heroku CLI
brew install heroku

# Login
heroku login

# Create app
heroku create agent-corex

# Deploy
git push heroku main

# Check logs
heroku logs --tail
```

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Init project
railway init

# Deploy
railway up
```

### Render
1. Push code to GitHub
2. Connect repository on render.com
3. Set environment variables
4. Deploy (automatic)

### Google Cloud Run
```bash
# Build and deploy
gcloud run deploy agent-corex \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### AWS Lambda (with API Gateway)
Use AWS SAM or serverless framework:
```bash
serverless deploy
```

---

## Systemd Service (Linux)

### Create Service File
```bash
sudo nano /etc/systemd/system/agent-corex.service
```

### Service Configuration
```ini
[Unit]
Description=Agent-Core Service
After=network.target

[Service]
Type=simple
User=agent-corex
WorkingDirectory=/opt/agent-corex
ExecStart=/usr/local/bin/uvicorn agent_core.api.main:app \
    --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5s

Environment="MCP_CONFIG=/etc/agent-corex/mcp.json"
Environment="LOG_LEVEL=info"

[Install]
WantedBy=multi-user.target
```

### Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable agent-corex
sudo systemctl start agent-corex
sudo systemctl status agent-corex
```

---

## Nginx Reverse Proxy

### Configuration
```nginx
upstream agent_corex {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.agent-corex.dev;

    location / {
        proxy_pass http://agent_corex;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS
```nginx
server {
    listen 443 ssl;
    server_name api.agent-corex.dev;

    ssl_certificate /etc/letsencrypt/live/agent-corex.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agent-corex.dev/privkey.pem;

    location / {
        proxy_pass http://agent_corex;
        # ... proxy headers ...
    }
}
```

---

## Environment Variables

### Essential
```bash
# MCP Configuration
MCP_CONFIG=/path/to/mcp.json

# Logging
LOG_LEVEL=info  # debug, info, warning, error
```

### Optional
```bash
# Server
HOST=0.0.0.0
PORT=8000

# Performance
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker

# Cache
CACHE_DIR=~/.cache/agent_core

# Database (Phase 2)
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Docker
docker logs -f <container-id>

# Kubernetes
kubectl logs -f deployment/agent-corex

# Systemd
sudo journalctl -u agent-corex -f

# File
tail -f /var/log/agent-corex.log
```

### Metrics (Phase 2)
Will include:
- Request count
- Response time
- Error rate
- Tool retrieval accuracy

---

## Security Checklist

- [ ] Use HTTPS/SSL in production
- [ ] Enable rate limiting (Phase 2)
- [ ] Add authentication (Phase 2)
- [ ] Keep dependencies updated
- [ ] Monitor for vulnerabilities
- [ ] Use environment variables for secrets
- [ ] Run behind reverse proxy (Nginx/HAProxy)
- [ ] Enable logging and monitoring
- [ ] Regular backups
- [ ] Security patches

---

## Performance Tuning

### Worker Processes
```bash
# More workers for high load
uvicorn agent_core.api.main:app --workers 4

# Single worker for development
uvicorn agent_core.api.main:app --workers 1
```

### Gunicorn (Production)
```bash
gunicorn agent_core.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Load Balancing
Deploy multiple instances behind load balancer:
```
Client
  ↓
Load Balancer (Nginx/HAProxy)
  ↓
[Server 1] [Server 2] [Server 3]
```

---

## Scaling

### Horizontal Scaling
- Deploy multiple instances
- Use load balancer
- Share configuration via environment
- Each instance is stateless

### Caching
- Cache tool listings (Phase 2)
- Cache embedding results (Phase 2)
- Use Redis for distributed cache (Phase 2)

### Optimization
- Pre-index tools on startup
- Use CDN for static assets
- Database connection pooling (Phase 2)

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn agent_core.api.main:app --port 8001
```

### Memory Issues
```bash
# Monitor memory
docker stats
free -h

# Reduce model cache
export CACHE_DIR=/small/disk/path
```

### Configuration Not Loading
```bash
# Check config path
echo $MCP_CONFIG
cat /path/to/mcp.json

# Validate JSON
python -m json.tool /path/to/mcp.json
```

---

## Backup & Recovery

### Backup Configuration
```bash
# Backup config files
tar -czf agent-corex-backup-$(date +%Y%m%d).tar.gz \
  /etc/agent-corex/ \
  /opt/agent-corex/config/
```

### Recovery
```bash
# Restore from backup
tar -xzf agent-corex-backup-*.tar.gz -C /
```

---

## Next Steps

1. ✅ Choose deployment platform
2. ✅ Set environment variables
3. ✅ Deploy application
4. ✅ Monitor health checks
5. ✅ Configure monitoring/alerts
6. ✅ Set up backups

---

**Last Updated**: March 2026
**Version**: 1.0.0
