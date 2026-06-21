# AMDI-OS Deployment Guide

This document describes the deployment procedures, environment configurations, and infrastructure setups for staging and production environments.

---

## 1. Local Deployment (Docker Compose)

For development, testing, and staging, AMDI-OS runs on Docker Compose.

### 1.1 Prerequisite Commands
Ensure Docker and Compose are installed, then boot the environment:
```bash
# Start all services (databases + API + celery worker + UI)
docker compose -f deployment/docker/docker-compose.yml up -d
```

### 1.2 Access Endpoints
* **API Service**: `http://localhost:8000`
* **React Dashboard**: `http://localhost:3000`
* **Qdrant Vector DB**: `http://localhost:6333`
* **Grafana (Monitoring)**: `http://localhost:3000` (credentials: `admin/admin`)

---

## 2. Production Deployment (Kubernetes)

For scalable production, AMDI-OS utilizes Kubernetes EKS and Helm.

### 2.1 Helm Deployment
```bash
# Add repositories and install chart
helm upgrade --install amdi-os ./deployment/helm/amdi-os \
  --namespace amdi-os --create-namespace \
  --values ./deployment/helm/amdi-os/values-production.yaml
```

### 2.2 Horizontal Pod Autoscaling (HPA)
Deployments are configured to scale horizontally based on CPU and memory thresholds:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: amdi-os-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: amdi-os-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 3. Infrastructure as Code (Terraform)

AWS infrastructure is provisioned using Terraform.

### 3.1 Initializing Infrastructure
```bash
cd deployment/terraform
terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan
```

### 3.2 Resources Provisioned
* **EKS Cluster**: Kubernetes Cluster running version 1.28.
* **Amazon RDS**: Multi-AZ PostgreSQL for relational schema storage.
* **ElastiCache Redis**: Clustered Redis for caching, rate limiting, and queue management.
* **Qdrant Cloud**: Managed vector database.
* **S3 Buckets**: Relational backup storage.