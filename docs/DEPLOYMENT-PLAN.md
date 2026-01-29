# Deployment Plan

## QR Code Generator Infrastructure & Deployment

**Version:** 1.0  
**Date:** January 2026  
**Status:** Draft under review

---

## 1. Overview

This document defines the deployment architecture, CI/CD pipelines, infrastructure configuration, and operational procedures for the QR Code Generator system.

---

## 2. Environment Strategy

### 2.1 Environments

| Environment | Purpose | URL | Data |
|-------------|---------|-----|------|
| Development | Local development | localhost:8000 | Mock/local DB |
| Staging | Pre-production testing | example.com | Sanitized production copy |
| Production | Live service | example.com | Real data |

### 2.2 Environment Configuration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENVIRONMENT PROMOTION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Development          Staging              Production                       │
│   ┌─────────┐         ┌─────────┐          ┌─────────┐                     │
│   │  Local  │  ────▶  │  Auto   │  ────▶   │  Manual │                     │
│   │  Build  │  (PR)   │  Deploy │  (Tag)   │ Approval│                     │
│   └─────────┘         └─────────┘          └─────────┘                     │
│                                                                              │
│   Triggers:           Triggers:            Triggers:                        │
│   - git push          - PR merge           - Version tag                    │
│   - manual            - main branch        - Manual trigger                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Configuration Management

```yaml
# Environment Variables (via AWS Secrets Manager / Kubernetes Secrets)

# Database
DATABASE_URL: postgresql://user:pass@host:5432/db
DATABASE_POOL_SIZE: 20
DATABASE_MAX_OVERFLOW: 10

# Redis
REDIS_URL: redis://host:6379/0
REDIS_PASSWORD: ${REDIS_PASSWORD}

# Storage
S3_BUCKET: qr-generator-${ENV}
S3_REGION: us-east-1
AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

# Auth
JWT_SECRET: ${JWT_SECRET}
JWT_ALGORITHM: HS256
JWT_EXPIRY_MINUTES: 15

# API
API_HOST: 0.0.0.0
API_PORT: 8000
API_WORKERS: 4
DEBUG: false

# External Services
SENDGRID_API_KEY: ${SENDGRID_API_KEY}
GEOIP_DATABASE_PATH: /data/geoip/GeoLite2-City.mmdb
```

---

## 3. Infrastructure Architecture

### 3.1 Cloud Architecture (AWS)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS Infrastructure                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CloudFlare                                    │   │
│  │                    (WAF, DDoS, CDN, DNS)                             │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────┼──────────────────────────────────────┐   │
│  │                           VPC                                        │   │
│  │                                                                      │   │
│  │  ┌───────────────────────────┼───────────────────────────────────┐ │   │
│  │  │                     Public Subnet                              │ │   │
│  │  │                                                                │ │   │
│  │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │ │   │
│  │  │  │     ALB     │    │   NAT GW    │    │   Bastion   │       │ │   │
│  │  │  │ (HTTPS LB)  │    │             │    │   (SSH)     │       │ │   │
│  │  │  └──────┬──────┘    └─────────────┘    └─────────────┘       │ │   │
│  │  │         │                                                      │ │   │
│  │  └─────────┼──────────────────────────────────────────────────────┘ │   │
│  │            │                                                         │   │
│  │  ┌─────────┼──────────────────────────────────────────────────────┐ │   │
│  │  │         │              Private Subnet                          │ │   │
│  │  │         ▼                                                      │ │   │
│  │  │  ┌─────────────────────────────────────────────────────────┐  │ │   │
│  │  │  │                    EKS Cluster                           │  │ │   │
│  │  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │ │   │
│  │  │  │  │API Pods │  │API Pods │  │ Worker  │  │ Worker  │   │  │ │   │
│  │  │  │  │ (x3)    │  │ (x3)    │  │ Pods    │  │ Pods    │   │  │ │   │
│  │  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │  │ │   │
│  │  │  └─────────────────────────────────────────────────────────┘  │ │   │
│  │  │                                                                │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                      Data Subnet                                │ │   │
│  │  │                                                                 │ │   │
│  │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │ │   │
│  │  │  │    RDS      │    │ ElastiCache │    │     S3      │        │ │   │
│  │  │  │ PostgreSQL  │    │   Redis     │    │   Bucket    │        │ │   │
│  │  │  │ (Multi-AZ)  │    │  (Cluster)  │    │             │        │ │   │
│  │  │  └─────────────┘    └─────────────┘    └─────────────┘        │ │   │
│  │  │                                                                 │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Kubernetes Resources

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qr-api
  labels:
    app: qr-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: qr-api
  template:
    metadata:
      labels:
        app: qr-api
    spec:
      containers:
      - name: api
        image: qr-generator/api:${VERSION}
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        envFrom:
        - secretRef:
            name: qr-api-secrets
        - configMapRef:
            name: qr-api-config
---
# api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: qr-api
spec:
  selector:
    app: qr-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
# api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: qr-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: qr-api
  minReplicas: 3
  maxReplicas: 20
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

### 3.3 Worker Deployment

```yaml
# worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qr-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: qr-worker
  template:
    metadata:
      labels:
        app: qr-worker
    spec:
      containers:
      - name: worker
        image: qr-generator/worker:${VERSION}
        command: ["celery", "-A", "app.worker", "worker", "-l", "info"]
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        envFrom:
        - secretRef:
            name: qr-api-secrets
        - configMapRef:
            name: qr-api-config
```

---

## 4. CI/CD Pipeline

### 4.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │  Code   │──▶│  Build  │──▶│  Test   │──▶│  Scan   │──▶│ Package │      │
│  │  Push   │   │         │   │         │   │         │   │         │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                                                                │             │
│                                                                ▼             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │   Go   │◀──│ Monitor │◀──│ Deploy  │◀──│ Approve │◀──│ Publish │      │
│  │  Live   │   │         │   │  Prod   │   │  (Prod) │   │  Image  │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│                     │                                                        │
│                     ▼                                                        │
│              ┌─────────────┐                                                │
│              │  Rollback   │ (if needed)                                    │
│              │  Procedure  │                                                │
│              └─────────────┘                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Set version
        id: version
        run: |
          if [[ $GITHUB_REF == refs/tags/* ]]; then
            echo "version=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "version=sha-${GITHUB_SHA::8}" >> $GITHUB_OUTPUT
          fi
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Lint
        run: |
          ruff check src/
          black --check src/
      
      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security-scan:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Bandit
        uses: jpetrucciani/bandit-check@main
        with:
          path: src/
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'

  package:
    runs-on: ubuntu-latest
    needs: [build, security-scan]
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.version }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy-staging:
    runs-on: ubuntu-latest
    needs: package
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}
      
      - name: Deploy to staging
        run: |
          kubectl set image deployment/qr-api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.version }} \
            -n staging
          kubectl rollout status deployment/qr-api -n staging

  deploy-production:
    runs-on: ubuntu-latest
    needs: [package, deploy-staging]
    if: startsWith(github.ref, 'refs/tags/v')
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}
      
      - name: Deploy to production
        run: |
          kubectl set image deployment/qr-api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.version }} \
            -n production
          kubectl rollout status deployment/qr-api -n production
      
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 Deployed ${{ needs.build.outputs.version }} to production"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### 4.3 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5. Monitoring & Observability

### 5.1 Metrics (Prometheus)

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'qr-api'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: qr-api
        action: keep
```

**Key Metrics:**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `http_requests_total` | Total HTTP requests | N/A |
| `http_request_duration_seconds` | Request latency | P99 > 1s |
| `qr_generations_total` | QR codes generated | N/A |
| `qr_generation_duration_seconds` | QR generation time | P99 > 2s |
| `redirects_total` | Dynamic QR redirects | N/A |
| `redirect_latency_seconds` | Redirect latency | P99 > 100ms |
| `errors_total` | Error count by type | > 10/min |
| `active_connections` | DB connections | > 80% pool |

### 5.2 Logging (ELK Stack)

```python
# Structured logging configuration
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# Example log output
{
    "timestamp": "2026-01-28T12:00:00.000Z",
    "level": "info",
    "event": "qr_generated",
    "qr_id": "qr_abc123",
    "user_id": "usr_xyz",
    "type": "dynamic",
    "duration_ms": 156,
    "request_id": "req_123"
}
```

### 5.3 Alerting

```yaml
# alertmanager-rules.yaml
groups:
  - name: qr-generator
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99 latency above 1 second"
          
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections above 80%"
```

### 5.4 Dashboards (Grafana)

**Dashboard Panels:**

1. **Overview**
   - Request rate (req/s)
   - Error rate (%)
   - P50/P95/P99 latency
   - Active users

2. **QR Generation**
   - Generations per minute
   - Generation latency
   - By type (static/dynamic)
   - By format (PNG/SVG/etc.)

3. **Redirects**
   - Redirects per second
   - Redirect latency
   - Cache hit rate
   - Geographic distribution

4. **Infrastructure**
   - CPU/Memory usage
   - Pod count
   - Database connections
   - Redis memory

---

## 6. Disaster Recovery

### 6.1 Backup Strategy

| Component | Backup Frequency | Retention | Recovery Time |
|-----------|------------------|-----------|---------------|
| PostgreSQL | Daily full, hourly WAL | 30 days | < 1 hour |
| Redis | Every 15 min RDB | 24 hours | < 15 min |
| S3 | Versioning + replication | 30 days | Instant |
| Secrets | Manual export | Secure vault | < 30 min |

### 6.2 Recovery Procedures

```markdown
## Database Recovery

1. Identify failure point
2. Stop application writes
3. Restore from latest backup:
   ```bash
   pg_restore -h $DB_HOST -U $DB_USER -d qr_generator backup.sql
   ```
4. Apply WAL logs to failure point
5. Verify data integrity
6. Resume application

## Complete Region Failover

1. DNS failover to DR region (automatic via Route 53)
2. Verify DR database is current (< 1 hour lag)
3. Scale up DR Kubernetes cluster
4. Update CDN origins
5. Verify service health
6. Notify stakeholders
```

### 6.3 RTO/RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single pod failure | 0 (auto-heal) | 0 |
| Node failure | < 5 min | 0 |
| Zone failure | < 15 min | 0 |
| Region failure | < 4 hours | < 1 hour |
| Data corruption | < 4 hours | < 1 hour |

---

## 7. Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Security scan clean
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Stakeholders notified
- [ ] Change request approved

### Deployment

- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Verify metrics/logs
- [ ] Deploy to production (canary)
- [ ] Monitor error rates
- [ ] Gradual rollout (25% → 50% → 100%)
- [ ] Verify all pods healthy

### Post-Deployment

- [ ] Verify key user flows
- [ ] Check error rates
- [ ] Monitor performance metrics
- [ ] Update documentation
- [ ] Close change request
- [ ] Retrospective (if issues)

---

## 8. Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/qr-api -n production

# Rollback to specific version
kubectl rollout undo deployment/qr-api -n production --to-revision=5

# Verify rollback
kubectl rollout status deployment/qr-api -n production

# Check pods
kubectl get pods -n production -l app=qr-api
```

**Rollback Triggers:**
- Error rate > 5%
- P99 latency > 2x normal
- Critical functionality broken
- Security vulnerability discovered

---

*Document Owner: DevOps Team*  
*Last Updated: January 2026*
