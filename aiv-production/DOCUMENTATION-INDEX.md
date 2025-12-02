# Documentation Index - AIV Production Deployment

This repository contains comprehensive documentation for deploying JupyterHub to AIV's production Kubernetes infrastructure with enterprise-grade security, high availability, and full integration with AIV systems.

## 🚀 Quick Start

**New to AIV deployment? Start here:**

1. **[README.md](README.md)** – AIV production overview and prerequisites
2. **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** – **Start here!** Complete checklist
3. **[QUICK-START-GUIDE.md](QUICK-START-GUIDE.md)** – 7-step deployment guide
4. **[docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md)** – Complete 6-phase deployment

## 📚 Core Documentation

### AIV-Specific Guides

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md) | **Complete checklist** of what to get from AIV IT | **Start here** - before anything else |
| [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) | **6-phase deployment guide** for AIV production | Primary deployment guide |
| [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) | **7-step quick start** for AIV | Fast deployment path |
| [LAB-vs-PRODUCTION.md](LAB-vs-PRODUCTION.md) | **Comparison** between lab and AIV environments | Understanding differences |

### Setup and Operations

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [README.md](README.md) | AIV production overview | First stop for AIV deployment |
| [DETAILED-SETUP-GUIDE.md](DETAILED-SETUP-GUIDE.md) | Comprehensive setup guide | Detailed configuration reference |
| [STEP-BY-STEP.md](STEP-BY-STEP.md) | High-level checklist | Quick reference |
| [docs/admin-runbook.md](docs/admin-runbook.md) | **Operations manual** | Day-to-day management and troubleshooting |

### Specialized Topics

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [docs/ssl-tls-guide.md](docs/ssl-tls-guide.md) | **Corporate TLS/SSL** setup with AIV CA | Configuring corporate certificates |
| [docs/multi-user-auth-guide.md](docs/multi-user-auth-guide.md) | **Entra ID authentication** configuration | Setting up Azure AD integration |
| [docs/ci-cd.md](docs/ci-cd.md) | **GitLab CI/CD** pipelines | Automated builds with AIV GitLab |
| [docs/architecture.md](docs/architecture.md) | **Architecture overview** | Understanding the system design |
| [docs/user-guide.md](docs/user-guide.md) | **End-user documentation** | Share with AIV users |

## 🔧 Configuration Files

### Infrastructure Manifests

```
infra/
├── namespaces.yaml              # Namespace and RBAC for AIV
├── storage/
│   └── pvc-home.yaml           # Ceph storage configuration
├── network/
│   └── ingress.yaml            # Ingress with corporate TLS
├── monitoring/
│   ├── servicemonitor.yaml     # AIV Prometheus integration
│   └── grafana-dashboard-v1.json  # Grafana dashboard
└── jupyterhub/
    └── values-aiv-production.yaml  # AIV production config
```

### Container Images

```
images/
└── base-notebook/
    └── Dockerfile              # Base notebook (pushed to AIV Artifactory)
```

### Scripts

```
scripts/
├── build_base_image.sh         # Build and push to Artifactory
├── deploy-aiv-production.sh    # Deploy to AIV production
├── delete_jhub_v1.sh           # Uninstall JupyterHub
└── smoke_test_v1.sh            # Health checks
```

### CI/CD Workflows

```
ci-cd/gitlab/
└── .gitlab-ci.yml              # GitLab pipeline for AIV
```

## 🎯 Use Case: Where to Look

### "I'm starting AIV deployment from scratch"

1. **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** - Get all info from AIV IT
2. **[QUICK-START-GUIDE.md](QUICK-START-GUIDE.md)** - Follow 7-step deployment
3. **[docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md)** - Detailed 6-phase guide

### "I need to know what to request from AIV IT"

- **[docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)** - Complete checklist covering:
  - Kubernetes cluster access
  - Entra ID app registration
  - Domain name and TLS certificates
  - Artifactory credentials
  - Storage class
  - GitLab access
  - Network configuration

### "I need to configure Entra ID authentication"

- **Main guide:** [docs/multi-user-auth-guide.md](docs/multi-user-auth-guide.md)
- **Quick reference:** [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) Phase 3
- **Values file:** `infra/jupyterhub/values-aiv-production.yaml`

### "I need to set up corporate TLS certificates"

- **Main guide:** [docs/ssl-tls-guide.md](docs/ssl-tls-guide.md)
- **Corporate CA section:** See "Option 3: Corporate CA"
- **Quick reference:** [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) Step 4

### "I need to configure GitLab CI/CD"

- **Main guide:** [docs/ci-cd.md](docs/ci-cd.md)
- **Pipeline file:** `ci-cd/gitlab/.gitlab-ci.yml`
- **Registry setup:** See Artifactory configuration

### "I need to troubleshoot production issues"

Check troubleshooting sections in:
- [docs/admin-runbook.md](docs/admin-runbook.md) – Operations and troubleshooting
- [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) – Deployment-specific issues
- [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) – Common problems and solutions

### "I need to understand the architecture"

- **[docs/architecture.md](docs/architecture.md)** - Complete architecture
- **[LAB-vs-PRODUCTION.md](LAB-vs-PRODUCTION.md)** - AIV-specific architecture diagrams

### "Users need help using JupyterHub"

- Share [docs/user-guide.md](docs/user-guide.md) with AIV users

### "I need to operate and maintain the deployment"

- **[docs/admin-runbook.md](docs/admin-runbook.md)** - Complete operations guide covering:
  - Upgrades
  - Rollbacks
  - Monitoring
  - Backups
  - User management
  - Troubleshooting

## 📋 Configuration Templates

| File | Purpose |
|------|---------|
| `aiv-config.env.template` | Environment variables for AIV production |
| `infra/jupyterhub/values-aiv-production.yaml` | JupyterHub Helm values for AIV |

Copy `aiv-config.env.template` to `aiv-config.env` and fill in values from AIV IT.

## 🔄 Deployment Phases

### Phase 1: Prerequisites (Week 1)
- Gather all information from AIV IT
- Verify cluster access
- Test Artifactory access

**Docs:** [docs/aiv-requirements-checklist.md](docs/aiv-requirements-checklist.md)

### Phase 2: Infrastructure Setup (Week 2)
- Create Kubernetes secrets
- Configure storage
- Set up network ingress

**Docs:** [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) Steps 1-4

### Phase 3: Application Deployment (Week 2-3)
- Deploy JupyterHub
- Configure Entra ID
- Test authentication

**Docs:** [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) Steps 5-7

### Phase 4: Integration (Week 3)
- Set up monitoring
- Configure GitLab CI/CD
- Import Grafana dashboards

**Docs:** [docs/ci-cd.md](docs/ci-cd.md), [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) Post-deployment

### Phase 5: Testing (Week 4)
- User acceptance testing
- GPU allocation testing
- Performance testing

**Docs:** [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) Phase 5

### Phase 6: Production Cutover (Week 5)
- Final deployment
- User training
- Handoff to AIV operations

**Docs:** [docs/aiv-deployment-guide.md](docs/aiv-deployment-guide.md) Phase 6, [docs/admin-runbook.md](docs/admin-runbook.md)

## 🆘 Getting Help

### AIV IT Support

For infrastructure issues, contact AIV IT:
- Kubernetes cluster problems
- Network/DNS issues
- Entra ID configuration
- Storage provisioning
- Certificate management
- GitLab access

### Application Support

For JupyterHub issues:

1. **Check logs:**
   ```bash
   kubectl logs -n jupyterhub-prod -l component=hub --tail=100
   kubectl get pods -n jupyterhub-prod
   kubectl describe pod <pod-name> -n jupyterhub-prod
   ```

2. **Review documentation:**
   - [docs/admin-runbook.md](docs/admin-runbook.md) - Operations guide
   - [QUICK-START-GUIDE.md](QUICK-START-GUIDE.md) - Troubleshooting section

3. **Check monitoring:**
   - Access AIV Grafana
   - Review metrics and alerts
   - Check ServiceMonitor status

## 🔗 External References

- **JupyterHub Documentation:** https://jupyterhub.readthedocs.io/
- **Zero to JupyterHub (Kubernetes):** https://z2jh.jupyter.org/
- **OAuthenticator (Entra ID):** https://oauthenticator.readthedocs.io/
- **AIV Documentation:** (Internal AIV links)
- **NVIDIA Device Plugin:** https://github.com/NVIDIA/k8s-device-plugin

## 📊 Documentation Map

```
┌─────────────────────────────────────────────────────────────┐
│                        README.md                            │
│                 (AIV Production Overview)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┬─────────────────────┐
        │                           │                     │
        ▼                           ▼                     ▼
┌────────────────┐      ┌──────────────────────┐   ┌────────────────┐
│aiv-requirements│      │aiv-deployment-guide  │   │ QUICK-START    │
│-checklist      │─────▶│(6 Phases)            │──▶│ (7 Steps)      │
│(Start Here!)   │      └──────────────────────┘   └────────────────┘
└────────────────┘                │
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                       ▼                     ▼
              ┌────────────────┐    ┌────────────────┐
              │ ssl-tls-guide  │    │ multi-user-    │
              │ (Corporate CA) │    │ auth (Entra ID)│
              └────────────────┘    └────────────────┘
                       │                     │
                       └──────────┬──────────┘
                                  ▼
                       ┌──────────────────────┐
                       │   admin-runbook      │
                       │   (Operations)       │
                       └──────────────────────┘
```

## ⚙️ Key Configuration Points

### Entra ID Configuration

Location: `infra/jupyterhub/values-aiv-production.yaml`

- Tenant ID (from AIV IT)
- Client ID (from AIV IT)
- Client Secret (stored in Kubernetes secret)
- Allowed groups (AIV AD groups)
- Admin groups (AIV AD admin groups)

### Storage Configuration

Location: `infra/jupyterhub/values-aiv-production.yaml`

- Storage class: `ceph-rbd` or `ceph-s3` (from AIV IT)
- Capacity: 50Gi (adjust as needed)
- Access mode: ReadWriteOnce (for Ceph RBD)

### Network Configuration

Location: `infra/network/ingress.yaml`

- Domain: `jupyterhub.aiv.internal` (from AIV IT)
- TLS secret: `aiv-corporate-tls`
- Ingress class: `nginx` (AIV standard)

### Registry Configuration

Location: `infra/jupyterhub/values-aiv-production.yaml`

- Registry: `artifactory.aiv.internal`
- Image name: `ml-platform/base-notebook`
- Pull secret: `aiv-artifactory-credentials`

---

**Note:** This is the **AIV Production** deployment documentation. For internal lab deployment, see the main repository directory.

---

**Last Updated:** December 2025  
**AIV Production Deployment**
