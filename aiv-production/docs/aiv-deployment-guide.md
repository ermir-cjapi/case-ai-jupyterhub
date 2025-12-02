# AIV Production Deployment Guide

This guide provides step-by-step instructions for deploying JupyterHub to the AIV production environment.

## Prerequisites

Before deploying to AIV, ensure you have completed all items in [aiv-requirements-checklist.md](aiv-requirements-checklist.md) and received the necessary information from AIV IT.

---

## Deployment Phases

### Phase 1: Initial Setup and Validation (AIV IT + You)

**Timeline:** Week 1-2

#### 1.1 Receive AIV Access and Credentials

From AIV IT, you should receive:

- [ ] Kubernetes cluster kubeconfig file
- [ ] Entra ID app registration details (tenant ID, client ID, client secret)
- [ ] AIV Artifactory/registry credentials
- [ ] GitLab Top Level Group access
- [ ] Corporate CA certificate for TLS
- [ ] Network information (load balancer IP, DNS name)

#### 1.2 Set Up Local Access to AIV Cluster

```bash
# On your workstation
mkdir -p ~/.kube/aiv
# Copy kubeconfig from AIV IT
cp aiv-kubeconfig.yaml ~/.kube/aiv/config

# Test connection
export KUBECONFIG=~/.kube/aiv/config
kubectl cluster-info
kubectl get nodes

# Verify you can access the jupyterhub-prod namespace
kubectl get namespace jupyterhub-prod
# If it doesn't exist, create it (if you have permissions)
```

#### 1.3 Authenticate to AIV Container Registry

```bash
# Login to AIV Artifactory
docker login artifactory.aiv.internal
Username: <provided-by-aiv-it>
Password: <provided-by-aiv-it>

# Verify access
docker pull artifactory.aiv.internal/test/hello-world || echo "Check with AIV IT about registry permissions"
```

#### 1.4 Set Up GitLab Access

```bash
# Clone the project repository to AIV GitLab (if not already done)
cd iav-jupyterhub
git remote add aiv-gitlab https://gitlab.aiv.internal/<top-level-group>/jupyterhub.git

# Push codebase (first time)
git push aiv-gitlab main
```

---

### Phase 2: Build and Push Container Images

**Timeline:** Week 2

#### 2.1 Review and Customize Dockerfile

```bash
# Review the base notebook Dockerfile
cat images/base-notebook/Dockerfile

# Add any AIV-specific packages or configurations
# Edit if needed for AIV requirements
```

#### 2.2 Build Image for AIV Registry

```bash
# Set environment variables
export REGISTRY="artifactory.aiv.internal"
export IMAGE_NAME="ml-platform/base-notebook"
export IMAGE_TAG="v1.0.0"  # Use semantic versioning for production

# Build the image
cd images/base-notebook
docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest

# Push to AIV registry
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
docker push ${REGISTRY}/${IMAGE_NAME}:latest
```

#### 2.3 Verify Image in AIV Registry

```bash
# Pull to verify
docker pull ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Or check via Artifactory web UI
# https://artifactory.aiv.internal
```

---

### Phase 3: Configure AIV-Specific Settings

**Timeline:** Week 2-3

#### 3.1 Create AIV Configuration File

```bash
# Create environment config
cat > aiv-production-config.env <<'EOF'
export ENVIRONMENT="aiv-production"

# Container Registry
export REGISTRY="artifactory.aiv.internal"
export IMAGE_NAME="ml-platform/base-notebook"
export IMAGE_TAG="v1.0.0"

# JupyterHub Configuration
export JHUB_NAMESPACE="jupyterhub-prod"
export JHUB_HOST="jupyterhub.aiv.internal"
export RELEASE_NAME="jhub-production"

# Kubernetes
export STORAGE_CLASS="ceph-rbd"  # Or ceph-s3, confirm with AIV IT
export VALUES_FILE="infra/jupyterhub/values-aiv-production.yaml"
export CHART_VERSION="2.0.0"

# AIV Entra ID (provided by AIV IT)
export AIV_ENTRA_TENANT_ID="<tenant-id>"
export AIV_ENTRA_CLIENT_ID="<client-id>"
# Don't put secret in file, will be set in Kubernetes secret

# Monitoring
export GRAFANA_URL="https://grafana.aiv.internal"
export PROMETHEUS_NAMESPACE="monitoring"
EOF

# Load config
source aiv-production-config.env
```

#### 3.2 Update values-aiv-production.yaml

Edit `infra/jupyterhub/values-aiv-production.yaml`:

```bash
# Update Entra ID settings
sed -i "s/AIV_TENANT_ID/${AIV_ENTRA_TENANT_ID}/" infra/jupyterhub/values-aiv-production.yaml
sed -i "s/AIV_CLIENT_ID/${AIV_ENTRA_CLIENT_ID}/" infra/jupyterhub/values-aiv-production.yaml

# Update image registry
sed -i "s|artifactory.aiv.internal/ml-platform/base-notebook|${REGISTRY}/${IMAGE_NAME}|" infra/jupyterhub/values-aiv-production.yaml
sed -i "s/tag: v1/tag: ${IMAGE_TAG}/" infra/jupyterhub/values-aiv-production.yaml

# Update storage class
sed -i "s/storageClass: ceph-rbd/storageClass: ${STORAGE_CLASS}/" infra/jupyterhub/values-aiv-production.yaml
```

Or edit manually with your preferred editor.

#### 3.3 Create Kubernetes Secrets

```bash
# Set kubectl context
export KUBECONFIG=~/.kube/aiv/config

# Create namespace if it doesn't exist
kubectl create namespace ${JHUB_NAMESPACE} || echo "Namespace already exists"

# Create TLS secret with corporate CA certificate
# (Certificate files provided by AIV IT)
kubectl -n ${JHUB_NAMESPACE} create secret tls aiv-corporate-tls \
  --cert=aiv-cert.crt \
  --key=aiv-cert.key

# Create Entra ID client secret
kubectl -n ${JHUB_NAMESPACE} create secret generic entra-id-credentials \
  --from-literal=client-secret="${AIV_ENTRA_CLIENT_SECRET}"

# Create Artifactory pull secret
kubectl -n ${JHUB_NAMESPACE} create secret docker-registry aiv-artifactory-credentials \
  --docker-server=artifactory.aiv.internal \
  --docker-username="${AIV_REGISTRY_USER}" \
  --docker-password="${AIV_REGISTRY_PASSWORD}" \
  --docker-email="${YOUR_EMAIL}"

# Verify secrets
kubectl -n ${JHUB_NAMESPACE} get secrets
```

#### 3.4 Apply Supporting Infrastructure

```bash
# Apply namespaces and RBAC
kubectl apply -f infra/namespaces.yaml

# Update namespace to jupyterhub-prod if needed
sed -i 's/jupyterhub-test/jupyterhub-prod/g' infra/storage/pvc-home.yaml
sed -i 's/jupyterhub-test/jupyterhub-prod/g' infra/network/ingress.yaml
sed -i 's/jupyterhub-test/jupyterhub-prod/g' infra/monitoring/servicemonitor.yaml

# Update ingress for AIV domain
sed -i 's/jupyterhub-test.example.internal/jupyterhub.aiv.internal/g' infra/network/ingress.yaml

# Apply storage
kubectl apply -f infra/storage/pvc-home.yaml

# Apply ingress
kubectl apply -f infra/network/ingress.yaml

# Apply monitoring (if Prometheus Operator is installed)
kubectl apply -f infra/monitoring/servicemonitor.yaml
```

---

### Phase 4: Deploy JupyterHub to AIV Staging/Dev

**Timeline:** Week 3

Deploy to AIV staging environment first (if available) to test the configuration.

#### 4.1 Add JupyterHub Helm Repository

```bash
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart
helm repo update
```

#### 4.2 Deploy to Staging

```bash
# Ensure you're using AIV cluster context
export KUBECONFIG=~/.kube/aiv/config
kubectl config current-context

# Deploy JupyterHub
helm upgrade --install ${RELEASE_NAME} jupyterhub/jupyterhub \
  --namespace ${JHUB_NAMESPACE} \
  --version ${CHART_VERSION} \
  --values ${VALUES_FILE} \
  --timeout 10m \
  --wait

# Watch deployment
kubectl -n ${JHUB_NAMESPACE} get pods -w
```

#### 4.3 Verify Deployment

```bash
# Check all pods are running
kubectl -n ${JHUB_NAMESPACE} get pods

# Check hub logs
kubectl -n ${JHUB_NAMESPACE} logs -l component=hub --tail=100

# Check proxy logs
kubectl -n ${JHUB_NAMESPACE} logs -l component=proxy --tail=100

# Check ingress
kubectl -n ${JHUB_NAMESPACE} get ingress

# Get service status
kubectl -n ${JHUB_NAMESPACE} get svc
```

#### 4.4 Test Access

```bash
# From AIV network or VPN
curl -k https://jupyterhub.aiv.internal/hub/health

# Should return: {"status": "ok"}
```

#### 4.5 Test Authentication

1. Open browser: `https://jupyterhub.aiv.internal`
2. Should redirect to Entra ID login
3. Log in with AIV credentials
4. Verify you land in JupyterHub spawn page
5. Start a server (select CPU-only profile first)
6. Verify JupyterLab loads
7. Test basic functionality:
   - Create a notebook
   - Run Python code
   - Test file persistence (create file, restart server, verify file exists)

#### 4.6 Test GPU Access (If Available)

1. Start a server with "GPU - Standard" profile
2. In JupyterLab terminal or notebook:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU device: {torch.cuda.get_device_name(0)}")
```

```bash
# In terminal
nvidia-smi
```

#### 4.7 Test Multi-User

- Have AIV colleagues log in
- Verify each gets their own pod
- Check resource isolation
- Test shared storage (`/shared/datasets`, `/shared/models`)

---

### Phase 5: Production Deployment

**Timeline:** Week 4

After successful staging/dev testing, deploy to production.

#### 5.1 Schedule Deployment Window

Coordinate with AIV:
- [ ] Production deployment window (date/time)
- [ ] Notification to users (if any existing service)
- [ ] Rollback plan
- [ ] On-call support contacts

#### 5.2 Pre-Deployment Checklist

- [ ] All staging tests passed
- [ ] AIV IT sign-off
- [ ] Production DNS configured (`jupyterhub.aiv.internal`)
- [ ] Production TLS certificate installed
- [ ] Monitoring dashboards ready
- [ ] Backup strategy confirmed
- [ ] Runbook reviewed with AIV operations team

#### 5.3 Deploy to Production

```bash
# Switch to production namespace (if different from staging)
export JHUB_NAMESPACE="jupyterhub-prod"

# Perform deployment (same commands as staging)
source aiv-production-config.env

helm upgrade --install ${RELEASE_NAME} jupyterhub/jupyterhub \
  --namespace ${JHUB_NAMESPACE} \
  --version ${CHART_VERSION} \
  --values ${VALUES_FILE} \
  --timeout 10m \
  --wait
```

#### 5.4 Post-Deployment Validation

```bash
# Run smoke tests
./scripts/smoke_test_v1.sh

# Check monitoring
open https://grafana.aiv.internal
# Import dashboard from infra/monitoring/grafana-dashboard-v1.json

# Verify metrics collection
kubectl -n ${JHUB_NAMESPACE} get servicemonitor
```

#### 5.5 User Acceptance Testing

- [ ] AIV test users log in
- [ ] Create and run notebooks
- [ ] Test GPU allocation
- [ ] Verify storage persistence
- [ ] Test shared datasets access
- [ ] Verify Entra ID group-based access control

---

### Phase 6: Handoff and Operations

**Timeline:** Week 4-5

#### 6.1 Train AIV Operations Team

Provide training on:
- JupyterHub architecture
- User management via Entra ID groups
- Monitoring and alerting
- Common troubleshooting
- Upgrade procedures
- Backup and restore

#### 6.2 Documentation Handoff

Provide AIV team with:
- [x] [docs/admin-runbook.md](admin-runbook.md) - Operations guide
- [x] [docs/user-guide.md](user-guide.md) - End-user guide
- [x] [docs/architecture.md](architecture.md) - Architecture overview
- [x] [LAB-vs-PRODUCTION.md](../LAB-vs-PRODUCTION.md) - Configuration comparison
- [x] This deployment guide

#### 6.3 Set Up Monitoring and Alerting

Work with AIV IT to configure:
- Prometheus alerts for JupyterHub health
- Grafana dashboards
- User notification channels (email, Slack, Teams, etc.)
- On-call rotation (if applicable)

#### 6.4 Backup Configuration

```bash
# Backup JupyterHub database
kubectl -n ${JHUB_NAMESPACE} exec -it hub-... -- \
  pg_dump -h postgres.aiv.internal -U jupyterhub jupyterhub > jupyterhub-backup-$(date +%Y%m%d).sql

# Backup Helm values
helm -n ${JHUB_NAMESPACE} get values ${RELEASE_NAME} > values-backup-$(date +%Y%m%d).yaml

# Document backup schedule with AIV IT
```

---

## Troubleshooting

### Issue: Pods Not Starting

```bash
# Check pod status
kubectl -n ${JHUB_NAMESPACE} get pods

# Describe problematic pod
kubectl -n ${JHUB_NAMESPACE} describe pod <pod-name>

# Check events
kubectl -n ${JHUB_NAMESPACE} get events --sort-by='.lastTimestamp'

# Common fixes:
# - Image pull errors: Verify registry credentials
# - Storage errors: Check PVC and StorageClass
# - GPU errors: Verify GPU nodes and device plugin
```

### Issue: Entra ID Authentication Failing

```bash
# Check hub logs
kubectl -n ${JHUB_NAMESPACE} logs -l component=hub | grep -i azure

# Verify callback URL matches Entra app registration
# Should be: https://jupyterhub.aiv.internal/hub/oauth_callback

# Check Entra ID app permissions in Azure Portal
```

### Issue: Users Can't Access Shared Storage

```bash
# Check PVC status
kubectl -n ${JHUB_NAMESPACE} get pvc

# Check if mounted correctly
kubectl -n ${JHUB_NAMESPACE} describe pod jupyter-<username>

# Verify Ceph storage is accessible
```

---

## Rollback Procedure

If issues occur in production:

```bash
# List Helm releases
helm -n ${JHUB_NAMESPACE} history ${RELEASE_NAME}

# Rollback to previous version
helm -n ${JHUB_NAMESPACE} rollback ${RELEASE_NAME} <REVISION>

# Verify rollback
kubectl -n ${JHUB_NAMESPACE} get pods
```

---

## Ongoing Maintenance

### Regular Tasks

**Daily:**
- Monitor active users and resource usage
- Check for pod failures

**Weekly:**
- Review user feedback
- Check disk usage on storage
- Verify backups are running

**Monthly:**
- Review and apply JupyterHub updates
- Update base notebook image with security patches
- Review and optimize resource allocations

**Quarterly:**
- Review Entra ID group memberships
- Audit user activity
- Update documentation

---

## Support Contacts

| Component | Contact | Documentation |
|-----------|---------|---------------|
| **JupyterHub Platform** | Your Team | This guide |
| **Kubernetes Cluster** | AIV IT - Infrastructure | AIV Runbooks |
| **Entra ID** | AIV IT - Identity | AIV Identity Docs |
| **Storage (Ceph)** | AIV IT - Storage | AIV Storage Docs |
| **Networking** | AIV IT - Network | AIV Network Docs |
| **GitLab** | AIV IT - DevOps | AIV GitLab Docs |

---

## Next Steps

After successful deployment:

1. **Monitor** - Watch metrics and user feedback for first 2 weeks
2. **Iterate** - Adjust resource limits and profiles based on actual usage
3. **Expand** - Add more integrations (e.g., data catalogs, MLflow, etc.)
4. **Optimize** - Fine-tune based on AIV's specific needs

---

**Deployment Success Criteria:**

- [x] All users can authenticate via Entra ID
- [x] Notebooks start within 2 minutes
- [x] GPU allocation works correctly
- [x] Storage persists across sessions
- [x] Shared datasets accessible
- [x] Monitoring dashboards operational
- [x] No critical errors in 48 hours
- [x] AIV operations team trained and confident

**Congratulations on deploying JupyterHub to AIV production!** 🎉

