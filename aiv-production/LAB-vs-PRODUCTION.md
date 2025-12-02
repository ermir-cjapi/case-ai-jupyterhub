# Lab vs Production: Side-by-Side Comparison

This document provides a complete comparison between your **Cloudflare lab environment** and the **AIV production environment**, showing exactly what differs and what stays the same.

## Quick Reference

| Aspect | Lab (Cloudflare) | AIV Production |
|--------|------------------|----------------|
| **Purpose** | Testing, learning, POC | Production ML platform |
| **Infrastructure** | Your NVIDIA server | AIV on-prem Kubernetes |
| **Domain** | `jupyterhub.yourcompany.com` | `jupyterhub.aiv.internal` |
| **Access** | Via Cloudflare Tunnel | Corporate network only |
| **TLS** | Cloudflare-managed (automatic) | Corporate CA certificate |
| **Auth** | GitHub OAuth (test) | Entra ID (Active Directory) |
| **Storage** | `local-path` (local disk) | `ceph-rbd` (Ceph S3) |
| **Registry** | GitHub Container Registry | AIV Artifactory/Registry |
| **CI/CD** | GitHub Actions | GitLab (Top Level Group) |
| **Monitoring** | Self-hosted Prometheus/Grafana | AIV Grafana/Prometheus |

---

## Network Architecture Comparison

### Lab Environment (Cloudflare Tunnel)

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet/Your Device                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
         https://jupyterhub.yourcompany.com
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   Cloudflare Edge Network                     │
│  ✓ DNS Resolution                                            │
│  ✓ TLS Termination (auto SSL cert)                          │
│  ✓ DDoS Protection                                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ Encrypted Cloudflare Tunnel
┌──────────────────────────────────────────────────────────────┐
│               Your NVIDIA Server (192.168.1.93)              │
│                                                              │
│  ┌────────────────────┐                                     │
│  │  cloudflared       │ (Cloudflare tunnel daemon)          │
│  │  daemon            │                                     │
│  └────────┬───────────┘                                     │
│           │                                                 │
│           ▼ HTTP (internal)                                 │
│  ┌────────────────────┐                                     │
│  │  Traefik Ingress   │ 192.168.1.93:80                     │
│  │  Controller        │                                     │
│  └────────┬───────────┘                                     │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────────┐      ┌──────────────────┐          │
│  │  JupyterHub        │◄─────┤ Prometheus       │          │
│  │  Pods              │      │ Grafana          │          │
│  └────────┬───────────┘      └──────────────────┘          │
│           │                                                 │
│           ▼                                                 │
│  ┌────────────────────┐                                     │
│  │  User Notebook     │ (GPU-enabled)                       │
│  │  Pods              │                                     │
│  └────────────────────┘                                     │
│                                                              │
│  Storage: local-path (local SSD/HDD)                        │
│  GPU: 1x NVIDIA GPU (nvidia-gpu-operator)                   │
└──────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- ✅ No public IP needed
- ✅ Works behind NAT/firewall
- ✅ Automatic SSL from Cloudflare
- ✅ Accessible from anywhere
- ✅ Single-node, simple setup

---

### AIV Production Environment

```
┌──────────────────────────────────────────────────────────────┐
│              AIV Corporate Network Users                      │
│              (on corporate network or VPN)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
         https://jupyterhub.aiv.internal
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   AIV Corporate DNS                           │
│  jupyterhub.aiv.internal → A → 10.x.x.x                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   AIV Load Balancer (HA)                      │
│  ✓ TLS Termination (Corporate CA cert)                       │
│  ✓ High Availability                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│            AIV On-Prem Kubernetes Cluster                     │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐             │
│  │ NGINX Ingress      │  │ NGINX Ingress      │ (HA)        │
│  │ Controller         │  │ Controller         │             │
│  └────────┬───────────┘  └────────┬───────────┘             │
│           │                       │                         │
│           └───────────┬───────────┘                         │
│                       ▼                                     │
│  ┌────────────────────────────────────────┐                 │
│  │  JupyterHub Service                    │                 │
│  │  ┌──────────┐  ┌──────────┐           │                 │
│  │  │ Hub Pod  │  │ Hub Pod  │ (HA)      │                 │
│  │  └──────────┘  └──────────┘           │                 │
│  └────────────────┬───────────────────────┘                 │
│                   │                                         │
│                   ▼                                         │
│  ┌─────────────────────────────────────────┐                │
│  │  User Notebook Pods (GPU-enabled)       │                │
│  │  - Spread across GPU nodes              │                │
│  │  - Auto-scaling based on demand         │                │
│  └─────────────────────────────────────────┘                │
│                                                              │
│  ┌─────────────────────────────────────────┐                │
│  │  Infrastructure Services                │                │
│  │  - Entra ID authentication              │                │
│  │  - Ceph/S3 storage (Rados Ceph)         │                │
│  │  - IAM resource provisioning            │                │
│  │  - Prometheus/Grafana monitoring        │                │
│  │  - Artifactory (container registry)     │                │
│  │  - GitLab (CI/CD & repos)               │                │
│  └─────────────────────────────────────────┘                │
│                                                              │
│  GPU Nodes: Multiple NVIDIA GPU servers (HPE/others)        │
│  CPU Nodes: HPE CPU Servers                                 │
│  Storage: Ceph cluster (distributed, HA)                    │
└──────────────────────────────────────────────────────────────┘
```

**Key characteristics:**
- ✅ High availability (multiple replicas)
- ✅ Enterprise-grade infrastructure
- ✅ Corporate security/compliance
- ✅ Integrated with AIV systems
- ✅ Internal network only

---

## Configuration Files Comparison

### Lab Environment Files

```
iav-jupyterhub/
├── infra/jupyterhub/
│   └── values-lab-cloudflare.yaml          ← Lab-specific config
├── .cloudflared/
│   └── config.yml.template                 ← Cloudflare tunnel config
├── scripts/
│   ├── setup-cloudflare-tunnel.sh          ← Cloudflare setup script
│   └── deploy-lab.sh                       ← Lab deployment wrapper
└── lab-config.env                          ← Lab environment variables
```

### AIV Production Files

```
iav-jupyterhub/
├── infra/jupyterhub/
│   └── values-aiv-production.yaml          ← AIV-specific config
├── infra/aiv/
│   ├── tls-certificate.yaml                ← Corporate CA cert (secret)
│   └── gitlab-registry-secret.yaml         ← GitLab registry credentials
├── scripts/
│   └── deploy-aiv-production.sh            ← AIV deployment script
├── docs/
│   ├── aiv-deployment-guide.md             ← AIV-specific deployment
│   └── aiv-requirements-checklist.md       ← What to get from AIV IT
└── aiv-production-config.env               ← AIV environment variables
```

---

## Detailed Configuration Comparison

### 1. Domain & DNS

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **Domain** | `jupyterhub.yourcompany.com` | `jupyterhub.aiv.internal` |
| **DNS Provider** | Cloudflare | AIV Corporate DNS |
| **DNS Type** | CNAME to Cloudflare Tunnel | A Record to Load Balancer |
| **Public Access** | Yes (via Cloudflare) | No (internal only) |
| **DNS Config** | Automatic via `cloudflared` | Manual by AIV IT team |

**Lab DNS Setup:**
```bash
# Automatic via cloudflared CLI
cloudflared tunnel route dns jupyterhub-tunnel jupyterhub.yourcompany.com
```

**AIV DNS Setup:**
```
# Done by AIV IT in their DNS server
jupyterhub.aiv.internal  IN  A  10.50.100.10
```

---

### 2. TLS/SSL Certificates

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **Certificate Source** | Cloudflare (automatic) | AIV Corporate CA |
| **Certificate Type** | Cloudflare Universal SSL | Enterprise SSL |
| **Renewal** | Automatic (Cloudflare) | Manual or enterprise PKI |
| **Trust** | Public (all browsers) | Corporate trust store |
| **Setup Complexity** | Low (automatic) | Medium (coordinate with IT) |

**Lab TLS:**
```yaml
# No TLS config in Kubernetes - Cloudflare handles everything
spec:
  rules:
    - host: jupyterhub.yourcompany.com
      # No tls: section needed
```

**AIV TLS:**
```yaml
# infra/network/ingress.yaml
spec:
  tls:
    - hosts:
        - jupyterhub.aiv.internal
      secretName: aiv-corporate-tls  # Corporate CA cert
  rules:
    - host: jupyterhub.aiv.internal
```

---

### 3. Authentication

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **Primary Auth** | GitHub OAuth | Entra ID (Azure AD) |
| **Identity Provider** | GitHub.com | AIV Entra ID tenant |
| **User Source** | GitHub accounts | Active Directory users |
| **Groups** | GitHub orgs/teams | Entra ID groups |
| **Admin Management** | GitHub usernames | AD security groups |

**Lab Auth Config:**
```yaml
# values-lab-cloudflare.yaml
hub:
  extraConfig:
    10-github-auth: |
      from oauthenticator.github import GitHubOAuthenticator
      c.JupyterHub.authenticator_class = GitHubOAuthenticator
      c.GitHubOAuthenticator.client_id = "YOUR_GITHUB_CLIENT_ID"
      c.GitHubOAuthenticator.client_secret = "YOUR_GITHUB_SECRET"
      c.GitHubOAuthenticator.oauth_callback_url = "https://jupyterhub.yourcompany.com/hub/oauth_callback"
      c.Authenticator.admin_users = {"your-github-username"}
```

**AIV Auth Config:**
```yaml
# values-aiv-production.yaml
hub:
  extraConfig:
    10-entra-id-auth: |
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      c.AzureAdOAuthenticator.tenant_id = "AIV_TENANT_ID"
      c.AzureAdOAuthenticator.client_id = "AIV_CLIENT_ID"
      c.AzureAdOAuthenticator.client_secret = "AIV_CLIENT_SECRET"
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.aiv.internal/hub/oauth_callback"
      c.AzureAdOAuthenticator.allowed_groups = {"jupyterhub-users"}
      c.AzureAdOAuthenticator.admin_groups = {"jupyterhub-admins"}
```

---

### 4. Container Registry

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **Registry** | GitHub Container Registry | AIV Artifactory/Jfrog |
| **URL** | `ghcr.io/your-username` | `artifactory.aiv.internal` |
| **Authentication** | GitHub PAT | AIV registry credentials |
| **Public Access** | Optional | No (internal only) |

**Lab Registry:**
```yaml
# values-lab-cloudflare.yaml
singleuser:
  image:
    name: ghcr.io/your-username/iav/base-notebook
    tag: v1
    pullPolicy: IfNotPresent
```

**AIV Registry:**
```yaml
# values-aiv-production.yaml
singleuser:
  image:
    name: artifactory.aiv.internal/ml-platform/base-notebook
    tag: v1
    pullPolicy: IfNotPresent
  imagePullSecrets:
    - name: aiv-artifactory-credentials
```

---

### 5. Storage

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **StorageClass** | `local-path` | `ceph-rbd` or `ceph-s3` |
| **Backend** | Local disk | Ceph distributed storage |
| **Shared Storage** | Single PVC (ReadWriteMany) | Ceph S3 or RBD |
| **Capacity** | Limited by local disk | Scalable (Ceph cluster) |
| **Backup** | Manual | Enterprise backup solution |

**Lab Storage:**
```yaml
# values-lab-cloudflare.yaml
singleuser:
  storage:
    type: dynamic
    capacity: 10Gi
    dynamic:
      storageClass: local-path  # k3s default
```

**AIV Storage:**
```yaml
# values-aiv-production.yaml
singleuser:
  storage:
    type: dynamic
    capacity: 50Gi  # Larger for production
    dynamic:
      storageClass: ceph-rbd  # AIV's Ceph storage
```

---

### 6. CI/CD Pipelines

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **Platform** | GitHub Actions | GitLab (Top Level Group) |
| **Workflow Location** | `.github/workflows/` | `.gitlab-ci.yml` |
| **Triggers** | Push to `main`, manual | Push to `main`, MR, scheduled |
| **Runners** | GitHub-hosted | AIV GitLab runners |
| **Secrets** | GitHub Secrets | GitLab CI/CD variables |

**Lab CI/CD:**
```yaml
# .github/workflows/build-image.yml
name: Build Base Notebook
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
```

**AIV CI/CD:**
```yaml
# .gitlab-ci.yml
stages:
  - build
  - deploy

build-image:
  stage: build
  image: docker:24
  script:
    - docker login artifactory.aiv.internal -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD
    - docker build -t artifactory.aiv.internal/ml-platform/base-notebook:$CI_COMMIT_SHA .
    - docker push artifactory.aiv.internal/ml-platform/base-notebook:$CI_COMMIT_SHA
```

---

### 7. Monitoring & Observability

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| **Prometheus** | Self-hosted in cluster | AIV Prometheus stack |
| **Grafana** | Self-hosted in cluster | AIV Grafana instance |
| **Dashboard** | Import JSON manually | Import to AIV Grafana |
| **Metrics Retention** | Limited (local storage) | Enterprise (long-term) |
| **Alerting** | Optional | AIV alerting system |

**Lab Monitoring:**
```bash
# Deploy Prometheus + Grafana in your cluster
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Import dashboard from infra/monitoring/grafana-dashboard-v1.json
```

**AIV Monitoring:**
```yaml
# ServiceMonitor points to AIV's Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: jupyterhub
  namespace: jupyterhub-prod
  labels:
    release: aiv-prometheus  # AIV's Prometheus release
```

---

## What Stays the Same

These components are **identical** in both environments:

### ✅ Docker Images
- Same `Dockerfile` for base notebook
- Same Python libraries, CUDA, ML frameworks
- Just built and pushed to different registries

### ✅ JupyterHub Configuration Structure
- Same Helm chart (jupyterhub/jupyterhub)
- Same spawner configuration
- Same resource limits/guarantees
- Same user profiles (CPU-only, GPU-standard, GPU-large)
- Same culling settings

### ✅ Kubernetes Manifests Structure
- Same namespace/RBAC pattern
- Same ServiceMonitor for Prometheus
- Same Grafana dashboard JSON
- Same pod security policies

### ✅ Scripts
- Same build/deploy script logic
- Just different environment variables

### ✅ Documentation
- All docs apply to both environments
- Just reference different domains/settings

---

## Environment Variables Comparison

### Lab Environment Variables

```bash
# lab-config.env
export ENVIRONMENT="lab-cloudflare"

# Container Registry
export REGISTRY="ghcr.io/your-username"
export IMAGE_NAME="iav/base-notebook"
export IMAGE_TAG="v1"

# JupyterHub Configuration
export JHUB_NAMESPACE="jupyterhub-test"
export JHUB_HOST="jupyterhub.yourcompany.com"
export RELEASE_NAME="jhub-lab"

# Kubernetes
export STORAGE_CLASS="local-path"
export VALUES_FILE="infra/jupyterhub/values-lab-cloudflare.yaml"
export CHART_VERSION="2.0.0"

# Cloudflare (specific to lab)
export CLOUDFLARE_TUNNEL_NAME="jupyterhub-tunnel"
export TRAEFIK_SERVICE="http://192.168.1.93:80"

# Monitoring
export GRAFANA_URL="http://localhost:3000"  # Port-forward to access
```

### AIV Production Variables

```bash
# aiv-production-config.env
export ENVIRONMENT="aiv-production"

# Container Registry
export REGISTRY="artifactory.aiv.internal"
export IMAGE_NAME="ml-platform/base-notebook"
export IMAGE_TAG="v1"

# JupyterHub Configuration
export JHUB_NAMESPACE="jupyterhub-prod"
export JHUB_HOST="jupyterhub.aiv.internal"
export RELEASE_NAME="jhub-production"

# Kubernetes
export STORAGE_CLASS="ceph-rbd"
export VALUES_FILE="infra/jupyterhub/values-aiv-production.yaml"
export CHART_VERSION="2.0.0"

# AIV-specific
export AIV_ENTRA_TENANT_ID="<provided-by-aiv-it>"
export AIV_ENTRA_CLIENT_ID="<provided-by-aiv-it>"
export AIV_LOAD_BALANCER_IP="10.50.100.10"  # Example

# Monitoring
export GRAFANA_URL="https://grafana.aiv.internal"
```

---

## Migration Checklist: Lab → AIV

When you're ready to deploy to AIV production:

### Phase 1: Gather AIV Information

- [ ] **Domain name** from AIV IT (e.g., `jupyterhub.aiv.internal`)
- [ ] **Kubernetes cluster access** (kubeconfig file)
- [ ] **Entra ID app registration details**:
  - [ ] Tenant ID
  - [ ] Client ID
  - [ ] Client Secret
  - [ ] Allowed groups for users
  - [ ] Admin groups
- [ ] **Corporate CA certificate** for TLS
- [ ] **Container registry details**:
  - [ ] Registry URL (e.g., `artifactory.aiv.internal`)
  - [ ] Credentials (username/password or token)
- [ ] **Storage class name** (e.g., `ceph-rbd`, `ceph-s3`)
- [ ] **GitLab access**:
  - [ ] Top Level Group URL
  - [ ] Repository permissions
  - [ ] CI/CD runner access
- [ ] **Monitoring endpoints**:
  - [ ] Grafana URL
  - [ ] Prometheus service name/namespace
- [ ] **Network details**:
  - [ ] Load balancer IP or ingress IP
  - [ ] Network policies (if any)
  - [ ] Firewall rules needed

### Phase 2: Prepare Configuration

- [ ] Create `values-aiv-production.yaml` from template
- [ ] Fill in all AIV-specific values
- [ ] Create TLS secret YAML with corporate cert
- [ ] Create registry credentials secret
- [ ] Update GitLab CI/CD pipeline for AIV registry
- [ ] Adjust resource limits based on AIV cluster capacity

### Phase 3: Test Build & Push

- [ ] Authenticate to AIV Artifactory
- [ ] Build base notebook image
- [ ] Push to AIV registry
- [ ] Verify image pull from AIV cluster

### Phase 4: Deploy to AIV Staging/Dev

- [ ] Deploy to AIV staging cluster first
- [ ] Verify pods start successfully
- [ ] Test Entra ID authentication
- [ ] Test user notebook spawning
- [ ] Test GPU allocation
- [ ] Verify storage persistence
- [ ] Check monitoring integration

### Phase 5: Production Cutover

- [ ] Schedule deployment window with AIV
- [ ] Deploy to AIV production cluster
- [ ] Run smoke tests
- [ ] Verify with AIV test users
- [ ] Monitor for 24-48 hours
- [ ] Hand off to AIV operations team

---

## Quick Command Reference

### Lab (Cloudflare) Commands

```bash
# Setup
cd iav-jupyterhub
source lab-config.env
./scripts/setup-cloudflare-tunnel.sh

# Build & Deploy
./scripts/build_base_image.sh
./scripts/deploy_jhub_v1.sh

# Access
open https://jupyterhub.yourcompany.com

# Monitor
kubectl logs -n jupyterhub-test -l component=hub --tail=50
kubectl get pods -n jupyterhub-test
```

### AIV Production Commands

```bash
# Setup (one-time)
cd iav-jupyterhub
source aiv-production-config.env

# Authenticate to AIV registry
docker login artifactory.aiv.internal

# Build & Deploy
./scripts/build_base_image.sh
./scripts/deploy-aiv-production.sh

# Access (from AIV network)
open https://jupyterhub.aiv.internal

# Monitor
kubectl logs -n jupyterhub-prod -l component=hub --tail=50
kubectl get pods -n jupyterhub-prod
```

---

## Support & Next Steps

### For Lab Environment

See comprehensive guides:
- [DETAILED-SETUP-GUIDE.md](DETAILED-SETUP-GUIDE.md) - Complete setup walkthrough
- [docs/ssl-tls-guide.md](docs/ssl-tls-guide.md) - TLS configuration
- [docs/multi-user-auth-guide.md](docs/multi-user-auth-guide.md) - Authentication options

### For AIV Production

See AIV-specific guides:
- [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) - AIV deployment steps
- [docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md) - What to request from AIV IT
- [docs/admin-runbook.md](docs/admin-runbook.md) - Operations guide

---

**Last Updated:** November 2025  
**Maintained by:** IAV JupyterHub Team

