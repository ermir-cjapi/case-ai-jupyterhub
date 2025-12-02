# Quick Start Guide - AIV Production Deployment

Deploy JupyterHub to AIV's production Kubernetes infrastructure with enterprise-grade security, high availability, and integration with AIV systems.

## Overview

This guide provides a streamlined deployment path for JupyterHub on AIV's production infrastructure with:
- ✅ Entra ID (Azure AD) authentication
- ✅ Corporate TLS certificates from AIV CA
- ✅ AIV Artifactory container registry
- ✅ Ceph distributed storage
- ✅ High availability configuration
- ✅ Integration with AIV monitoring (Prometheus/Grafana)
- ✅ GitLab CI/CD pipelines

## Prerequisites Checklist

Before starting, you **MUST** have all of the following from AIV IT. See **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** for the complete checklist.

### Required Information

- [ ] **Kubernetes cluster access** (kubeconfig file)
- [ ] **Domain name** (e.g., `jupyterhub.aiv.internal`)
- [ ] **Entra ID configuration**:
  - [ ] Tenant ID
  - [ ] Client ID
  - [ ] Client Secret
  - [ ] User groups (allowed users)
  - [ ] Admin groups (administrators)
- [ ] **AIV Artifactory**:
  - [ ] Registry URL (e.g., `artifactory.aiv.internal`)
  - [ ] Credentials (username/password or token)
- [ ] **Corporate TLS certificate** (PEM format):
  - [ ] Certificate file (.crt)
  - [ ] Private key file (.key)
- [ ] **Storage class name** (e.g., `ceph-rbd`, `ceph-s3`)
- [ ] **Load balancer IP** or ingress configuration
- [ ] **GitLab repository** access (Top Level Group)
- [ ] **Monitoring endpoints** (Grafana, Prometheus URLs)

## Quick Start (7 Steps)

### Step 1: Verify AIV Infrastructure Access

Test that you can access all required AIV systems:

```bash
# Test Kubernetes cluster access
export KUBECONFIG=~/.kube/aiv-config
kubectl cluster-info
kubectl get nodes

# Test Artifactory access
docker login artifactory.aiv.internal -u YOUR_USERNAME
# Enter password when prompted

# Verify corporate network/VPN
ping jupyterhub.aiv.internal  # Should resolve to load balancer IP
```

### Step 2: Configure Environment

```bash
cd aiv-production

# Create configuration file from template
cp aiv-config.env.template aiv-config.env

# Edit with AIV-specific values
nano aiv-config.env
```

Fill in all required values:

```bash
# Registry
export REGISTRY="artifactory.aiv.internal"
export REGISTRY_USERNAME="your-aiv-username"
export REGISTRY_PASSWORD="your-aiv-password"

# JupyterHub
export JHUB_HOST="jupyterhub.aiv.internal"
export STORAGE_CLASS="ceph-rbd"

# Entra ID (from AIV IT)
export AIV_ENTRA_TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AIV_ENTRA_CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
export AIV_ENTRA_CLIENT_SECRET="your-secret-value"

# ... etc
```

Load configuration:

```bash
source aiv-config.env
```

### Step 3: Build and Push Container Image

```bash
cd images/base-notebook

# Build image
docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .

# Push to AIV Artifactory
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Verify image is accessible
docker pull ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
```

### Step 4: Create Kubernetes Secrets

```bash
# Switch to AIV cluster context
export KUBECONFIG=~/.kube/aiv-config

# Create namespace
kubectl apply -f infra/namespaces.yaml

# TLS certificate (provided by AIV IT)
kubectl -n jupyterhub-prod create secret tls aiv-corporate-tls \
  --cert=/path/to/aiv-corporate.crt \
  --key=/path/to/aiv-corporate.key

# Artifactory registry credentials
kubectl -n jupyterhub-prod create secret docker-registry aiv-artifactory-credentials \
  --docker-server=${REGISTRY} \
  --docker-username=${REGISTRY_USERNAME} \
  --docker-password=${REGISTRY_PASSWORD}

# Entra ID OAuth credentials
kubectl -n jupyterhub-prod create secret generic entra-id-oauth \
  --from-literal=client-id=${AIV_ENTRA_CLIENT_ID} \
  --from-literal=client-secret=${AIV_ENTRA_CLIENT_SECRET} \
  --from-literal=tenant-id=${AIV_ENTRA_TENANT_ID}
```

### Step 5: Update JupyterHub Configuration

Edit `infra/jupyterhub/values-aiv-production.yaml`:

```yaml
# Update with your specific values
hub:
  extraConfig:
    10-entra-id-auth: |
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
      c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
      c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.aiv.internal/hub/oauth_callback"
      c.AzureAdOAuthenticator.allowed_groups = {"jupyterhub-users"}
      c.AzureAdOAuthenticator.admin_groups = {"jupyterhub-admins"}

singleuser:
  image:
    name: artifactory.aiv.internal/ml-platform/base-notebook
    tag: v1
  storage:
    dynamic:
      storageClass: ceph-rbd  # or your storage class
```

### Step 6: Deploy JupyterHub

```bash
# Deploy infrastructure
kubectl apply -f infra/storage/
kubectl apply -f infra/network/ingress.yaml
kubectl apply -f infra/monitoring/servicemonitor.yaml

# Deploy JupyterHub via script
./scripts/deploy-aiv-production.sh
```

Or deploy manually with Helm:

```bash
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo update

helm upgrade --install jhub-production jupyterhub/jupyterhub \
  --namespace jupyterhub-prod \
  --values infra/jupyterhub/values-aiv-production.yaml \
  --version ${CHART_VERSION} \
  --create-namespace
```

### Step 7: Verify and Access

```bash
# Wait for all pods to be ready
kubectl get pods -n jupyterhub-prod --watch

# Check hub logs
kubectl logs -n jupyterhub-prod -l component=hub --tail=100

# Verify ingress configuration
kubectl get ingress -n jupyterhub-prod

# Check service status
kubectl get svc -n jupyterhub-prod
```

Access JupyterHub from AIV corporate network:

```
https://jupyterhub.aiv.internal
```

**Note:** You must be on the AIV corporate network or connected via VPN.

## Post-Deployment Tasks

### Configure Monitoring

Import Grafana dashboard:

1. Access AIV Grafana: `https://grafana.aiv.internal`
2. Import dashboard from `infra/monitoring/grafana-dashboard-v1.json`
3. Verify metrics are being collected from ServiceMonitor

### Set Up CI/CD

Configure GitLab CI/CD pipeline:

1. Push code to AIV GitLab repository
2. Configure CI/CD variables in GitLab:
   - `CI_REGISTRY_USER` - Artifactory username
   - `CI_REGISTRY_PASSWORD` - Artifactory password
   - `KUBECONFIG` - Base64-encoded kubeconfig
3. The pipeline in `ci-cd/gitlab/.gitlab-ci.yml` will automatically build and deploy

### User Acceptance Testing

1. Test with AIV test users
2. Verify Entra ID authentication
3. Test GPU allocation
4. Verify persistent storage
5. Check monitoring dashboards

## Common Commands

### Check Deployment Status

```bash
# All pods in namespace
kubectl get pods -n jupyterhub-prod

# Hub logs
kubectl logs -n jupyterhub-prod -l component=hub -f

# User pods
kubectl get pods -n jupyterhub-prod | grep jupyter-

# Resource usage
kubectl top pods -n jupyterhub-prod
kubectl top nodes
```

### Update Configuration

```bash
# Edit values file
nano infra/jupyterhub/values-aiv-production.yaml

# Apply changes
helm upgrade jhub-production jupyterhub/jupyterhub \
  --namespace jupyterhub-prod \
  --values infra/jupyterhub/values-aiv-production.yaml \
  --version ${CHART_VERSION}

# Monitor rollout
kubectl rollout status deployment/hub -n jupyterhub-prod
```

### Scale Resources

```bash
# Increase hub replicas for HA
kubectl scale deployment/hub --replicas=3 -n jupyterhub-prod

# Check proxy replicas
kubectl get deployment/proxy -n jupyterhub-prod
```

### Rollback

```bash
# View release history
helm history jhub-production -n jupyterhub-prod

# Rollback to previous version
helm rollback jhub-production -n jupyterhub-prod

# Rollback to specific revision
helm rollback jhub-production 2 -n jupyterhub-prod
```

## Troubleshooting

### Authentication Issues

**Problem:** Users can't log in with Entra ID

```bash
# Check OAuth secret
kubectl get secret entra-id-oauth -n jupyterhub-prod -o yaml

# Verify callback URL in Entra ID app registration
# Must match: https://jupyterhub.aiv.internal/hub/oauth_callback

# Check hub logs for auth errors
kubectl logs -n jupyterhub-prod -l component=hub | grep -i auth
```

### Image Pull Issues

**Problem:** Pods stuck in `ImagePullBackOff`

```bash
# Check registry secret
kubectl get secret aiv-artifactory-credentials -n jupyterhub-prod

# Test image pull manually
docker pull artifactory.aiv.internal/ml-platform/base-notebook:v1

# Verify imagePullSecrets in deployment
kubectl describe pod <pod-name> -n jupyterhub-prod
```

### Storage Issues

**Problem:** User notebooks can't start due to storage

```bash
# Check PVC status
kubectl get pvc -n jupyterhub-prod

# Describe PVC for events
kubectl describe pvc claim-<username> -n jupyterhub-prod

# Verify storage class exists
kubectl get storageclass

# Check Ceph cluster health (if accessible)
```

### Network/DNS Issues

**Problem:** Can't access JupyterHub

```bash
# Test DNS resolution
nslookup jupyterhub.aiv.internal

# Check ingress
kubectl get ingress -n jupyterhub-prod
kubectl describe ingress jupyterhub -n jupyterhub-prod

# Verify load balancer
kubectl get svc -n jupyterhub-prod
```

### GPU Not Available

**Problem:** GPU not showing up in notebooks

```bash
# Check GPU resources on nodes
kubectl get nodes -o json | jq '.items[].status.allocatable."nvidia.com/gpu"'

# Check NVIDIA device plugin
kubectl get pods -n kube-system | grep nvidia

# Check pod GPU request
kubectl describe pod jupyter-<username> -n jupyterhub-prod | grep -A5 Requests
```

## Architecture

```
AIV Corporate Network Users
    ↓
Corporate DNS (jupyterhub.aiv.internal → 10.x.x.x)
    ↓
AIV Load Balancer (TLS with Corporate CA)
    ↓
AIV Kubernetes Cluster
    ├── NGINX Ingress (HA)
    ├── JupyterHub Hub Pods (HA)
    ├── JupyterHub Proxy
    ├── User Notebook Pods (GPU, auto-scaling)
    └── Infrastructure Services
        ├── Entra ID (authentication)
        ├── Ceph Storage (distributed)
        ├── Artifactory (registry)
        ├── Prometheus/Grafana (monitoring)
        └── GitLab (CI/CD)
```

## Documentation

### Essential Guides

- 📋 **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** - Complete requirements checklist
- 📖 **[docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md)** - 6-phase deployment guide
- 📊 **[LAB-vs-PRODUCTION.md](LAB-vs-PRODUCTION.md)** - Lab vs Production comparison
- 📝 **[DETAILED-SETUP-GUIDE.md](DETAILED-SETUP-GUIDE.md)** - Detailed setup instructions

### Reference Documentation

- 📐 **[docs/architecture.md](docs/architecture.md)** - Architecture overview
- 🔧 **[docs/admin-runbook.md](docs/admin-runbook.md)** - Operations manual
- 🔐 **[docs/ssl-tls-guide.md](docs/ssl-tls-guide.md)** - Corporate TLS setup
- 👥 **[docs/multi-user-auth-guide.md](docs/multi-user-auth-guide.md)** - Entra ID authentication
- ⚙️ **[docs/ci-cd.md](docs/ci-cd.md)** - GitLab CI/CD setup
- 📝 **[docs/user-guide.md](docs/user-guide.md)** - End-user documentation

## Support

### Before Requesting Support

1. Check troubleshooting section above
2. Review pod logs: `kubectl logs -n jupyterhub-prod`
3. Check AIV infrastructure status
4. Verify configuration in values file

### AIV IT Support

Contact AIV IT for:
- Kubernetes cluster access issues
- Network/DNS problems
- Entra ID authentication setup
- Storage provisioning
- Certificate renewal
- Load balancer configuration

### Application Support

For JupyterHub-specific issues:
- See [docs/admin-runbook.md](docs/admin-runbook.md)
- Review deployment logs
- Check Helm release status: `helm status jhub-production -n jupyterhub-prod`

---

**Ready to deploy?** Ensure you have completed the prerequisites checklist, then start with Step 1!
