# 🚀 Production Deployment Guide

Complete guide for deploying the Autonomous Full-Stack Application Factory to production environments.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Security Considerations](#security-considerations)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Scaling](#scaling)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 100GB+ SSD
- **Network**: Stable internet connection with low latency

### Software Requirements

- Docker 24.0+
- Docker Compose 2.0+
- Kubernetes 1.28+ (for K8s deployment)
- kubectl CLI
- Cloud provider CLI (AWS CLI, gcloud, or Azure CLI)

### API Keys Required

- Anthropic API key (Claude models)
- OpenAI API key (GPT models)

---

## Environment Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/fullstack-ai-factory.git
cd fullstack-ai-factory

# Create environment file
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env`:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Model Configuration
PRIMARY_MODEL=claude-sonnet-4-5
FAST_MODEL=gpt-4o-mini
REASONING_MODEL=claude-opus-4

# Database
DATABASE_URL=sqlite:///fullstack_factory.db
KNOWLEDGE_DB_URL=sqlite:///fullstack_knowledge.db

# Production Settings
DEPLOY_ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_TELEMETRY=true

# Security
SECRET_KEY=generate-strong-random-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Rate Limiting
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=60
```

### 3. Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended for Small Scale)

#### 1. Build and Start Services

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 2. Access Services

- **Streamlit UI**: http://localhost:8501
- **FastAPI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

#### 3. Stop Services

```bash
docker-compose down

# With volume cleanup
docker-compose down -v
```

### Option 2: Docker Swarm (For Multi-Node)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml fullstack-factory

# Check services
docker service ls

# Scale services
docker service scale fullstack-factory_api=3
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: yourdomain/fullstack-factory-api:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 4G
    environment:
      - DEPLOY_ENVIRONMENT=production
    networks:
      - fullstack-network
    volumes:
      - production-data:/app/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
      - ui
    networks:
      - fullstack-network

volumes:
  production-data:

networks:
  fullstack-network:
    driver: overlay
```

---

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace fullstack-factory
```

### 2. Create Secrets

```bash
kubectl create secret generic api-keys \
  --from-literal=anthropic-api-key=YOUR_KEY \
  --from-literal=openai-api-key=YOUR_KEY \
  -n fullstack-factory
```

### 3. Deploy Application

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fullstack-factory-api
  namespace: fullstack-factory
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fullstack-factory-api
  template:
    metadata:
      labels:
        app: fullstack-factory-api
    spec:
      containers:
      - name: api
        image: yourdomain/fullstack-factory-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-api-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "2000m"
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
  name: fullstack-factory-api-service
  namespace: fullstack-factory
spec:
  selector:
    app: fullstack-factory-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Apply:

```bash
kubectl apply -f k8s/deployment.yaml
```

### 4. Configure Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fullstack-factory-hpa
  namespace: fullstack-factory
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fullstack-factory-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Cloud Platform Deployment

### AWS Deployment

#### Option 1: AWS ECS (Elastic Container Service)

```bash
# Install AWS CLI
pip install awscli

# Configure AWS
aws configure

# Create ECR repository
aws ecr create-repository --repository-name fullstack-factory

# Build and push image
$(aws ecr get-login --no-include-email)
docker build -t fullstack-factory .
docker tag fullstack-factory:latest AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/fullstack-factory:latest
docker push AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/fullstack-factory:latest

# Create ECS cluster
aws ecs create-cluster --cluster-name fullstack-factory-cluster

# Create task definition (see ecs-task-definition.json)
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster fullstack-factory-cluster \
  --service-name fullstack-factory-service \
  --task-definition fullstack-factory \
  --desired-count 3 \
  --launch-type FARGATE
```

#### Option 2: AWS EC2 with Auto Scaling

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name fullstack-factory-template \
  --version-description "v1" \
  --launch-template-data file://launch-template.json

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name fullstack-factory-asg \
  --launch-template LaunchTemplateName=fullstack-factory-template \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 3
```

### GCP Deployment

#### Google Cloud Run

```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash

# Initialize
gcloud init

# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/fullstack-factory
gcloud run deploy fullstack-factory \
  --image gcr.io/PROJECT_ID/fullstack-factory \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 4 \
  --min-instances 2 \
  --max-instances 10
```

#### Google Kubernetes Engine (GKE)

```bash
# Create cluster
gcloud container clusters create fullstack-factory-cluster \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --region us-central1

# Deploy application
kubectl apply -f k8s/
```

### Azure Deployment

#### Azure Container Instances

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Create resource group
az group create --name fullstack-factory-rg --location eastus

# Create container
az container create \
  --resource-group fullstack-factory-rg \
  --name fullstack-factory \
  --image yourdomain/fullstack-factory:latest \
  --dns-name-label fullstack-factory \
  --ports 8000 8501
```

---

## Security Considerations

### 1. SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. API Key Management

Use secret management services:

- **AWS**: AWS Secrets Manager
- **GCP**: Google Secret Manager
- **Azure**: Azure Key Vault

```python
# Example: AWS Secrets Manager
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

### 3. Network Security

- Use VPC/Private networks
- Configure security groups/firewall rules
- Enable DDoS protection
- Implement rate limiting

### 4. Authentication

```python
# Add authentication middleware
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/generate")
async def generate_application(
    request: GenerationRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401)
    # Continue...
```

---

## Monitoring and Logging

### 1. Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fullstack-factory'
    static_configs:
      - targets: ['api:8000']
```

### 2. Grafana Dashboards

Import pre-built dashboards:
- System metrics
- API performance
- Agent execution time
- Error rates

### 3. Log Aggregation

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /app/logs/*.log
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### 4. Alerting

```yaml
# alertmanager.yml
route:
  receiver: 'email'
  
receivers:
- name: 'email'
  email_configs:
  - to: 'ops@yourdomain.com'
    from: 'alerts@yourdomain.com'
```

---

## Scaling

### Horizontal Scaling

```bash
# Docker Swarm
docker service scale fullstack-factory_api=5

# Kubernetes
kubectl scale deployment fullstack-factory-api --replicas=5

# Auto-scaling based on metrics
kubectl autoscale deployment fullstack-factory-api \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

### Vertical Scaling

```yaml
# Increase resources
resources:
  requests:
    memory: "8Gi"
    cpu: "2000m"
  limits:
    memory: "16Gi"
    cpu: "4000m"
```

---

## Backup and Recovery

### 1. Database Backup

```bash
# Backup SQLite databases
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

sqlite3 fullstack_factory.db ".backup '$BACKUP_DIR/factory_$DATE.db'"
sqlite3 fullstack_knowledge.db ".backup '$BACKUP_DIR/knowledge_$DATE.db'"
```

### 2. Volume Backup

```bash
# Kubernetes
kubectl exec -it POD_NAME -- tar czf - /app/data | \
  gzip > backup_$(date +%Y%m%d).tar.gz

# Docker
docker run --rm --volumes-from CONTAINER_NAME \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/backup.tar.gz /app/data
```

### 3. Automated Backups

```yaml
# CronJob for backups
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-job
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-image
            command: ["/backup.sh"]
```

---

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

```bash
# Check memory
docker stats

# Increase limits
docker update --memory="16g" CONTAINER_ID
```

#### 2. API Rate Limits

```python
# Implement exponential backoff
import time
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(min=1, max=60))
def call_api():
    # API call
    pass
```

#### 3. Database Locks

```bash
# Check for locks
sqlite3 factory.db "PRAGMA busy_timeout = 10000;"

# Or migrate to PostgreSQL for production
```

#### 4. Container Crashes

```bash
# View logs
docker logs CONTAINER_ID

# Inspect container
docker inspect CONTAINER_ID

# Check resource usage
docker stats CONTAINER_ID
```

---

## Production Checklist

- [ ] SSL/TLS configured
- [ ] API keys secured in secret manager
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Auto-scaling configured
- [ ] Rate limiting enabled
- [ ] Logging centralized
- [ ] Health checks configured
- [ ] Disaster recovery plan documented
- [ ] Performance tested under load
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on operations

---

## Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Review monitoring dashboards
- Contact: devops@yourdomain.com

---

**Last Updated**: January 2025