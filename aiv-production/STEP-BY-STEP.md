# JupyterHub AIV Production - Step-by-Step Guide

This guide is a **high-level checklist** for deploying JupyterHub to AIV's production Kubernetes infrastructure.

📖 **For detailed instructions**, see:
- **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** – **Start here!** Prerequisites checklist
- **[docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md)** – Complete 6-phase deployment guide
- **[QUICK-START-GUIDE.md](QUICK-START-GUIDE.md)** – 7-step quick start
- **[docs/ssl-tls-guide.md](docs/ssl-tls-guide.md)** – Corporate TLS certificate setup
- **[docs/multi-user-auth-guide.md](docs/multi-user-auth-guide.md)** – Entra ID authentication

## Prerequisites - **DO THIS FIRST!**

See **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** for the complete checklist.

You **MUST** have from AIV IT:

- [ ] Kubernetes cluster access (kubeconfig)
- [ ] Domain name (e.g., jupyterhub.aiv.internal)
- [ ] Entra ID credentials (Tenant ID, Client ID, Secret)
- [ ] Corporate TLS certificate (.crt and .key files)
- [ ] Artifactory access (registry URL, credentials)
- [ ] Storage class name (e.g., ceph-rbd)
- [ ] Load balancer IP
- [ ] GitLab repository access
- [ ] Monitoring endpoints (Grafana, Prometheus URLs)

## Step 1: Verify AIV Infrastructure Access

- [ ] Test Kubernetes cluster access
- [ ] Test Artifactory login
- [ ] Verify network connectivity

```bash
export KUBECONFIG=~/.kube/aiv-config
kubectl cluster-info
kubectl get nodes

docker login artifactory.aiv.internal
```

## Step 2: Configure Environment

- [ ] Copy configuration template
- [ ] Fill in AIV-specific values
- [ ] Load configuration

```bash
cp aiv-config.env.template aiv-config.env
nano aiv-config.env  # Fill in all AIV values
source aiv-config.env
```

## Step 3: Build and Push Container Image

- [ ] Build notebook image
- [ ] Push to AIV Artifactory
- [ ] Verify image is accessible

```bash
cd images/base-notebook
docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
docker pull ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}  # Verify
```

## Step 4: Create Kubernetes Secrets

- [ ] Create namespace
- [ ] Create TLS certificate secret
- [ ] Create registry credentials secret
- [ ] Create Entra ID OAuth secret

```bash
# Namespace
kubectl apply -f infra/namespaces.yaml

# TLS certificate
kubectl -n jupyterhub-prod create secret tls aiv-corporate-tls \
  --cert=/path/to/aiv-corporate.crt \
  --key=/path/to/aiv-corporate.key

# Artifactory credentials
kubectl -n jupyterhub-prod create secret docker-registry aiv-artifactory-credentials \
  --docker-server=${REGISTRY} \
  --docker-username=${REGISTRY_USERNAME} \
  --docker-password=${REGISTRY_PASSWORD}

# Entra ID OAuth
kubectl -n jupyterhub-prod create secret generic entra-id-oauth \
  --from-literal=client-id=${AIV_ENTRA_CLIENT_ID} \
  --from-literal=client-secret=${AIV_ENTRA_CLIENT_SECRET} \
  --from-literal=tenant-id=${AIV_ENTRA_TENANT_ID}
```

## Step 5: Configure JupyterHub Values

- [ ] Review `infra/jupyterhub/values-aiv-production.yaml`
- [ ] Update Entra ID configuration
- [ ] Set allowed groups and admin groups
- [ ] Configure storage class
- [ ] Set resource limits
- [ ] Verify image registry path

Key sections to update:
- Entra ID OAuth configuration
- Storage class (ceph-rbd)
- Image registry (artifactory.aiv.internal)
- Resource limits for production

## Step 6: Deploy Infrastructure

- [ ] Apply storage manifests
- [ ] Apply network ingress
- [ ] Apply monitoring ServiceMonitor

```bash
kubectl apply -f infra/storage/
kubectl apply -f infra/network/ingress.yaml
kubectl apply -f infra/monitoring/servicemonitor.yaml
```

## Step 7: Deploy JupyterHub

- [ ] Add JupyterHub Helm repository
- [ ] Deploy JupyterHub

```bash
./scripts/deploy-aiv-production.sh
```

Or manually:

```bash
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update

helm upgrade --install jhub-production jupyterhub/jupyterhub \
  --namespace jupyterhub-prod \
  --values infra/jupyterhub/values-aiv-production.yaml \
  --version 2.0.0 \
  --create-namespace \
  --timeout 15m \
  --wait
```

## Step 8: Verify Deployment

- [ ] Check all pods are running
- [ ] Review hub logs
- [ ] Check ingress configuration
- [ ] Verify secrets are mounted

```bash
kubectl get pods -n jupyterhub-prod
kubectl logs -n jupyterhub-prod -l component=hub --tail=100
kubectl get ingress -n jupyterhub-prod
kubectl describe ingress jupyterhub -n jupyterhub-prod
```

## Step 9: Test Entra ID Authentication

- [ ] Access JupyterHub (from AIV network)
- [ ] Test Entra ID login
- [ ] Verify group membership
- [ ] Test admin access

```
https://jupyterhub.aiv.internal
```

- [ ] Login with AIV credentials
- [ ] Verify user is in allowed group
- [ ] Test admin functions (if in admin group)

## Step 10: Test GPU Allocation

- [ ] Spawn notebook with GPU profile
- [ ] Test CUDA availability
- [ ] Verify GPU assignment

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

## Step 11: Configure Monitoring

- [ ] Access AIV Grafana
- [ ] Import JupyterHub dashboard
- [ ] Verify metrics are being collected
- [ ] Set up alerts (if needed)

```bash
# Dashboard location
infra/monitoring/grafana-dashboard-v1.json

# Import to AIV Grafana
open ${GRAFANA_URL}  # https://grafana.aiv.internal
```

## Step 12: Set Up GitLab CI/CD

- [ ] Push code to AIV GitLab
- [ ] Configure CI/CD variables
- [ ] Test pipeline

CI/CD variables to set in GitLab:
- `CI_REGISTRY_USER` - Artifactory username
- `CI_REGISTRY_PASSWORD` - Artifactory password
- `KUBECONFIG` - Base64-encoded kubeconfig

## Step 13: User Acceptance Testing

- [ ] Test with AIV test users
- [ ] Verify authentication works
- [ ] Test notebook spawning
- [ ] Test GPU allocation
- [ ] Verify storage persistence
- [ ] Test notebook sharing
- [ ] Verify monitoring dashboards

## Step 14: Production Handoff

- [ ] Document configuration
- [ ] Train AIV operations team
- [ ] Set up support procedures
- [ ] Create runbook for operations
- [ ] Schedule regular maintenance

See [docs/admin-runbook.md](docs/admin-runbook.md)

## Common Commands

### Check Status
```bash
kubectl get pods -n jupyterhub-prod
kubectl get svc -n jupyterhub-prod
kubectl get ingress -n jupyterhub-prod
kubectl top pods -n jupyterhub-prod
```

### View Logs
```bash
kubectl logs -n jupyterhub-prod -l component=hub --tail=100 -f
kubectl logs -n jupyterhub-prod -l component=proxy --tail=50
```

### Update Deployment
```bash
source aiv-config.env
helm upgrade jhub-production jupyterhub/jupyterhub \
  --namespace jupyterhub-prod \
  --values infra/jupyterhub/values-aiv-production.yaml
```

### Rollback
```bash
helm history jhub-production -n jupyterhub-prod
helm rollback jhub-production -n jupyterhub-prod
```

### Scale
```bash
kubectl scale deployment/hub --replicas=3 -n jupyterhub-prod
```

## Troubleshooting

### Authentication Issues
```bash
# Check Entra ID secret
kubectl get secret entra-id-oauth -n jupyterhub-prod -o yaml

# Verify callback URL matches Entra ID app
# Should be: https://jupyterhub.aiv.internal/hub/oauth_callback

# Check hub logs for auth errors
kubectl logs -n jupyterhub-prod -l component=hub | grep -i auth
```

### Image Pull Issues
```bash
# Verify registry secret
kubectl get secret aiv-artifactory-credentials -n jupyterhub-prod

# Test image pull
docker pull ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Check pod events
kubectl describe pod <pod-name> -n jupyterhub-prod
```

### Storage Issues
```bash
# Check PVCs
kubectl get pvc -n jupyterhub-prod

# Verify storage class
kubectl get storageclass

# Check PVC events
kubectl describe pvc claim-<username> -n jupyterhub-prod
```

### Network Issues
```bash
# Test DNS
nslookup jupyterhub.aiv.internal

# Check ingress
kubectl describe ingress jupyterhub -n jupyterhub-prod

# Verify TLS secret
kubectl get secret aiv-corporate-tls -n jupyterhub-prod
```

### GPU Issues
```bash
# Check GPU availability
kubectl get nodes -o json | jq '.items[].status.allocatable."nvidia.com/gpu"'

# Check NVIDIA device plugin
kubectl get pods -n kube-system | grep nvidia

# Check GPU assignment
kubectl describe pod jupyter-<username> -n jupyterhub-prod | grep -A5 Requests
```

## Support

### AIV IT Support

Contact AIV IT for:
- Kubernetes cluster issues
- Network/DNS problems
- Entra ID configuration
- Storage provisioning
- Certificate renewal
- GitLab access

### Application Support

For JupyterHub issues:
- [docs/admin-runbook.md](docs/admin-runbook.md) - Operations manual
- [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) - Deployment guide
- [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) - Troubleshooting section

## Next Steps

1. Monitor production usage
2. Set up regular backups
3. Configure automated updates
4. Train end users
5. Establish support procedures
6. Plan capacity expansion

## Documentation

- **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** - Prerequisites
- **[docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md)** - Complete deployment
- **[docs/admin-runbook.md](docs/admin-runbook.md)** - Operations
- **[LAB-vs-PRODUCTION.md](LAB-vs-PRODUCTION.md)** - Comparison
- **[DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md)** - All documentation

---

**AIV Production Deployment**
