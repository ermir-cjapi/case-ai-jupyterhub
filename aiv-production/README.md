# JupyterHub on Kubernetes - AIV Production Deployment

This project provides a **production-ready JupyterHub deployment** for AIV's enterprise Kubernetes infrastructure with Entra ID authentication, corporate networking, and enterprise-grade security.

## Key Features

- **GPU-enabled** notebook environment with CUDA support
- **Entra ID (Azure AD)** authentication with group-based access control
- **Corporate TLS** certificates from AIV CA
- **Ceph distributed storage** for scalability and redundancy
- **High availability** with multiple replicas
- **AIV Artifactory** container registry integration
- **GitLab CI/CD** pipelines
- **Enterprise monitoring** with AIV Prometheus/Grafana
- **Internal network only** - compliant with AIV security policies

## Directory Layout

- `infra/` – Kubernetes manifests and Helm values for AIV environment
- `images/` – Dockerfiles for notebook images
- `ci-cd/` – GitLab CI/CD configuration
- `docs/` – Architecture and operational documentation
- `scripts/` – Helper scripts for build, deploy, and testing

## Prerequisites

Before you begin, you **must** obtain the following from AIV IT:

### Required from AIV IT Team

- [ ] **Kubernetes cluster access** (kubeconfig file)
- [ ] **Entra ID app registration**:
  - Tenant ID
  - Client ID
  - Client Secret
  - Authorized user/admin groups
- [ ] **Domain name**: e.g., `jupyterhub.aiv.internal`
- [ ] **Corporate TLS certificate** (from AIV CA)
- [ ] **Artifactory credentials**:
  - Registry URL (e.g., `artifactory.aiv.internal`)
  - Username and password/token
- [ ] **Storage class name**: e.g., `ceph-rbd` or `ceph-s3`
- [ ] **GitLab repository access** (Top Level Group)
- [ ] **Load balancer IP** or ingress configuration
- [ ] **Monitoring integration** (Grafana/Prometheus endpoints)

📋 **See [docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md) for the complete checklist**

## Quick Start

### 1. Verify Prerequisites

Ensure you have all required information from AIV IT and can access:

```bash
# Test Kubernetes cluster access
export KUBECONFIG=~/.kube/aiv-config
kubectl cluster-info
kubectl get nodes

# Test Artifactory access
docker login artifactory.aiv.internal
```

### 2. Configure Environment

```bash
cp aiv-config.env.template aiv-config.env
nano aiv-config.env  # Fill in all AIV-specific values
source aiv-config.env
```

### 3. Build and Push Container Image

```bash
# Build base notebook image
cd images/base-notebook
docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .

# Push to AIV Artifactory
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
```

### 4. Create Kubernetes Secrets

```bash
# TLS certificate secret (provided by AIV IT)
kubectl -n $JHUB_NAMESPACE create secret tls aiv-corporate-tls \
  --cert=${TLS_CERT_PATH} \
  --key=${TLS_KEY_PATH}

# Artifactory registry credentials (if not using service accounts)
kubectl -n $JHUB_NAMESPACE create secret docker-registry aiv-artifactory-credentials \
  --docker-server=${REGISTRY} \
  --docker-username=${REGISTRY_USERNAME} \
  --docker-password=${REGISTRY_PASSWORD}

# Entra ID OAuth credentials
kubectl -n $JHUB_NAMESPACE create secret generic entra-id-oauth \
  --from-literal=client-id=${AIV_ENTRA_CLIENT_ID} \
  --from-literal=client-secret=${AIV_ENTRA_CLIENT_SECRET} \
  --from-literal=tenant-id=${AIV_ENTRA_TENANT_ID}
```

### 5. Deploy Infrastructure

```bash
# Create namespace and RBAC
kubectl apply -f infra/namespaces.yaml

# Deploy storage (if not using dynamic provisioning)
kubectl apply -f infra/storage/

# Deploy network ingress
kubectl apply -f infra/network/ingress.yaml

# Deploy monitoring ServiceMonitor
kubectl apply -f infra/monitoring/servicemonitor.yaml
```

### 6. Deploy JupyterHub

```bash
./scripts/deploy-aiv-production.sh
```

Or manually:

```bash
helm upgrade --install ${RELEASE_NAME} jupyterhub/jupyterhub \
  --namespace ${JHUB_NAMESPACE} \
  --values infra/jupyterhub/values-aiv-production.yaml \
  --version ${CHART_VERSION} \
  --create-namespace
```

### 7. Verify Deployment

```bash
# Check pods are running
kubectl get pods -n $JHUB_NAMESPACE

# Check hub logs
kubectl logs -n $JHUB_NAMESPACE -l component=hub --tail=100

# Verify ingress
kubectl get ingress -n $JHUB_NAMESPACE
```

### 8. Access JupyterHub

From the AIV corporate network or VPN:

```
https://jupyterhub.aiv.internal
```

**Note:** Access is only available from within the AIV network or through VPN.

## Configuration

### Entra ID Authentication

The deployment uses Entra ID for authentication. Configuration in `infra/jupyterhub/values-aiv-production.yaml`:

```yaml
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
```

### Storage Configuration

Uses AIV's Ceph distributed storage:

```yaml
singleuser:
  storage:
    type: dynamic
    capacity: 50Gi
    dynamic:
      storageClass: ceph-rbd  # or ceph-s3
```

### High Availability

Production deployment includes:
- Multiple hub replicas
- Multiple proxy replicas
- Distributed storage
- Load balancer for ingress

## Architecture

```
AIV Corporate Network
    ↓
Corporate DNS (jupyterhub.aiv.internal → Load Balancer)
    ↓
AIV Load Balancer (TLS termination with Corporate CA)
    ↓
AIV Kubernetes Cluster
    ├── NGINX Ingress Controllers (HA)
    ├── JupyterHub Hub Pods (HA)
    ├── JupyterHub Proxy Pods
    ├── User Notebook Pods (GPU-enabled, auto-scaling)
    ├── Ceph Storage (distributed)
    └── Infrastructure Services
        ├── Entra ID authentication
        ├── Artifactory (container registry)
        ├── Prometheus/Grafana (monitoring)
        └── GitLab (CI/CD)
```

## CI/CD with GitLab

The GitLab pipeline is configured in `ci-cd/gitlab/.gitlab-ci.yml`:

```yaml
stages:
  - build
  - deploy

build-image:
  stage: build
  script:
    - docker build -t artifactory.aiv.internal/ml-platform/base-notebook:$CI_COMMIT_SHA .
    - docker push artifactory.aiv.internal/ml-platform/base-notebook:$CI_COMMIT_SHA

deploy-production:
  stage: deploy
  script:
    - helm upgrade --install jhub-production jupyterhub/jupyterhub \
        --namespace jupyterhub-prod \
        --values infra/jupyterhub/values-aiv-production.yaml
  when: manual
  only:
    - main
```

## Monitoring

### Grafana Dashboard

Import the dashboard from `infra/monitoring/grafana-dashboard-v1.json` into AIV Grafana:

```bash
# Dashboard will be available at
open https://grafana.aiv.internal
```

### Prometheus Metrics

The deployment exposes metrics via ServiceMonitor for AIV's Prometheus:

```bash
kubectl get servicemonitor -n $JHUB_NAMESPACE
```

## Operations

### Common Commands

```bash
# Check deployment status
kubectl get pods -n jupyterhub-prod

# View hub logs
kubectl logs -n jupyterhub-prod -l component=hub --tail=100 -f

# Restart hub
kubectl rollout restart deployment/hub -n jupyterhub-prod

# Scale user capacity
kubectl get pods -n jupyterhub-prod | grep jupyter-

# Check resource usage
kubectl top nodes
kubectl top pods -n jupyterhub-prod
```

### Upgrades

```bash
# Update configuration
nano infra/jupyterhub/values-aiv-production.yaml

# Apply upgrade
helm upgrade jhub-production jupyterhub/jupyterhub \
  --namespace jupyterhub-prod \
  --values infra/jupyterhub/values-aiv-production.yaml \
  --version $NEW_CHART_VERSION

# Monitor rollout
kubectl rollout status deployment/hub -n jupyterhub-prod
```

### Rollback

```bash
# View release history
helm history jhub-production -n jupyterhub-prod

# Rollback to previous version
helm rollback jhub-production -n jupyterhub-prod
```

## Troubleshooting

### Entra ID Authentication Issues

```bash
# Check OAuth configuration
kubectl get secret entra-id-oauth -n jupyterhub-prod -o yaml

# Verify callback URL matches Entra ID app registration
# Should be: https://jupyterhub.aiv.internal/hub/oauth_callback
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n jupyterhub-prod

# Check storage class
kubectl get storageclass

# Describe PVC for events
kubectl describe pvc claim-<username> -n jupyterhub-prod
```

### Network/Ingress Issues

```bash
# Check ingress
kubectl get ingress -n jupyterhub-prod
kubectl describe ingress jupyterhub -n jupyterhub-prod

# Test DNS resolution
nslookup jupyterhub.aiv.internal

# Check load balancer
kubectl get svc -n jupyterhub-prod
```

### GPU Allocation Issues

```bash
# Check GPU availability
kubectl get nodes -o json | jq '.items[].status.allocatable'

# Check nvidia device plugin
kubectl get pods -n kube-system | grep nvidia
```

## Documentation

### Deployment Guides

- 📖 **[docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md)** – Complete 6-phase deployment guide
- 📋 **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** – Requirements checklist
- 📊 **[LAB-vs-PRODUCTION.md](LAB-vs-PRODUCTION.md)** – Comparison with lab environment
- 📝 **[DETAILED-SETUP-GUIDE.md](DETAILED-SETUP-GUIDE.md)** – Detailed setup instructions

### Reference Guides

- 📐 **[docs/architecture.md](docs/architecture.md)** – Architecture overview
- 🔧 **[docs/admin-runbook.md](docs/admin-runbook.md)** – Operations manual
- 🔐 **[docs/ssl-tls-guide.md](docs/ssl-tls-guide.md)** – Corporate TLS setup
- 👥 **[docs/multi-user-auth-guide.md](docs/multi-user-auth-guide.md)** – Entra ID configuration
- 📝 **[docs/user-guide.md](docs/user-guide.md)** – End-user documentation
- ⚙️ **[docs/ci-cd.md](docs/ci-cd.md)** – CI/CD with GitLab

## Security Considerations

- ✅ **Internal network only** - No public internet access
- ✅ **Entra ID authentication** - Corporate identity management
- ✅ **Group-based access control** - Admin/user separation
- ✅ **Corporate TLS certificates** - Trusted by all AIV systems
- ✅ **Network policies** - Isolated namespaces
- ✅ **Container security** - Signed images from AIV Artifactory
- ✅ **Audit logging** - Integration with AIV SIEM

## Support

### AIV IT Support

For infrastructure issues, contact AIV IT:
- Kubernetes cluster issues
- Network/DNS problems
- Entra ID authentication
- Storage provisioning
- Certificate renewal

### Application Support

For JupyterHub configuration and operational issues:
- See [docs/admin-runbook.md](docs/admin-runbook.md)
- Check troubleshooting sections above
- Review logs: `kubectl logs -n jupyterhub-prod`

---

**Last Updated:** December 2025  
**AIV Production Deployment**
