# Internal Deployment Guide

This guide covers deploying the Agentic EDA tool to Dell's internal container platform.

## Prerequisites

- Access to Dell's internal container registry
- Access to Dell's Kubernetes cluster
- Docker installed locally
- kubectl configured for Dell's K8s cluster

## Build and Push Docker Image

### 1. Login to Internal Registry
```bash
docker login <INTERNAL_REGISTRY_URL>
```

### 2. Build Docker Image
```bash
docker build -t <INTERNAL_REGISTRY>/agentic-de-lifecycle:latest .
```

### 3. Push to Internal Registry
```bash
docker push <INTERNAL_REGISTRY>/agentic-de-lifecycle:latest
```

## Deploy to Kubernetes

### 1. Update Deployment Manifest
Edit `k8s-deployment.yaml` and replace:
- `<INTERNAL_REGISTRY>` with your actual internal registry URL

### 2. Apply Deployment
```bash
kubectl apply -f k8s-deployment.yaml
```

### 3. Check Deployment Status
```bash
kubectl get pods
kubectl get svc
```

### 4. Get Service URL
```bash
kubectl get svc agentic-eda-service
```

## Access the Application

Once deployed, access the application via the LoadBalancer service URL or internal DNS.

## Configuration

### Database Mode
The Database Mode requires network access to internal databases. Ensure:
- The pod has network policies allowing access to `ddlgpmprd11.us.dell.com:6420`
- Database credentials are provided via the UI (not hardcoded)

### File Upload Mode
File Upload Mode works without any external dependencies.

## Troubleshooting

### Pod Not Starting
```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
```

### Database Connection Issues
- Verify network policies allow DB access
- Check if hostname resolves from within the cluster
- Test connectivity from pod: `kubectl exec -it <pod-name> -- ping ddlgpmprd11.us.dell.com`

### Resource Limits
Adjust resource limits in `k8s-deployment.yaml` if needed:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

## CI/CD Integration

For automated deployments, integrate with Dell's CI/CD pipeline:
1. Build image on code push
2. Push to internal registry
3. Trigger Kubernetes deployment
4. Run smoke tests
