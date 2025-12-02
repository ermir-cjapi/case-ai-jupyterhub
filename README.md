# JupyterHub on Kubernetes

GPU-enabled JupyterHub for your NVIDIA server.

## Structure

```
├── local-testing/     # Test locally with Docker Compose
├── k8s-manifests/     # Plain Kubernetes YAML files (learn step-by-step)
├── helm/              # Helm deployment (one-command deploy)
├── images/            # Custom notebook image
└── aiv-production/    # AIV production deployment (separate)
```

## 🎯 Choose Your Deployment Method

### Option 1: Kubernetes Manifests (Recommended for Learning)
See every resource clearly, understand each component.

```bash
# 1. Enable GPU sharing (IMPORTANT for multi-user!)
cd k8s-manifests
./setup-gpu-timeslicing.sh  # Converts 1 GPU → 4 users
cd ..

# 2. Build image
source lab-config.env
docker login
./images/build_base_image.sh

# 3. Generate secret
openssl rand -hex 32
# Update k8s-manifests/02-secrets.yaml line 11

# 4. Configure Azure AD
# Edit k8s-manifests/01-configmap.yaml lines 44-47

# 5. Deploy
cd k8s-manifests
./deploy_k8s_manifests.sh

# Done! Access at https://jupyterhub.ccrolabs.com
```

**See:** `k8s-manifests/README.md` for detailed explanation of each resource.

### Option 2: Helm (Quick & Clean)
One command, Helm manages everything.

```bash
# 1. Enable GPU sharing (IMPORTANT for multi-user!)
cd helm
./setup-gpu-timeslicing.sh  # Converts 1 GPU → 4 users
cd ..

# 2. Build image
source lab-config.env
docker login
./images/build_base_image.sh

# 3. Generate secret
openssl rand -hex 32
# Update helm/values-helm.yaml line 6

# 4. Configure Azure AD
# Edit helm/values-helm.yaml lines 32-46

# 5. Deploy
cd helm
./deploy_jhub_helm.sh

# Done! Access at https://jupyterhub.ccrolabs.com
```

## Configuration

**K8s Manifests:** Edit `k8s-manifests/01-configmap.yaml`  
**Helm:** Edit `helm/values-helm.yaml`

Both configure:
- Authentication (GitHub, Azure AD, or none)
- Resource limits (CPU, RAM, GPU)
- Storage settings
- Admin users

## Cloudflare Setup

Cloudflare tunnel handles ingress:
1. Cloudflare dashboard → Tunnel → jupyterhub.ccrolabs.com
2. Points to: `http://localhost:80` (Traefik on k3s)
3. JupyterHub service → proxy-public → port 80

**No ingress resource needed** - Cloudflare connects directly.

## Common Commands

```bash
# Status
kubectl get pods -n jupyterhub-test

# Logs
kubectl logs -n jupyterhub-test -l component=hub

# Redeploy (K8s manifests)
cd k8s-manifests && ./deploy_k8s_manifests.sh

# Redeploy (Helm)
cd helm && ./deploy_jhub_helm.sh

# Delete (K8s manifests)
cd k8s-manifests && ./delete_k8s_manifests.sh

# Delete (Helm)
cd helm && ./delete_jhub_helm.sh
```

## 🎮 GPU Support & Multi-User Sharing

### GPU is Enabled by Default
**K8s Manifests:** `k8s-manifests/01-configmap.yaml` lines 36-37  
**Helm:** `helm/values-helm.yaml` lines 114-117

### ⚠️ Important: Enable GPU Sharing First!

**Without GPU sharing:**
- 1 RTX 5090 → Only 1 user at a time
- Other users wait indefinitely (Pending pods)

**With GPU sharing (time-slicing):**
- 1 RTX 5090 → 4 users simultaneously
- Each gets ~25% when all active, 100% when alone

### Enable GPU Sharing

```bash
# For Helm deployment
cd helm && ./setup-gpu-timeslicing.sh

# For K8s manifests deployment
cd k8s-manifests && ./setup-gpu-timeslicing.sh
```

**See:** `helm/GPU-SHARING.md` or `k8s-manifests/GPU-SHARING.md` for details

---

**Local testing?** See `local-testing/` folder  
**AIV production?** See `aiv-production/` folder
