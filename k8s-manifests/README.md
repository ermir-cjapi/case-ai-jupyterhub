# Kubernetes Manifests for JupyterHub

Plain Kubernetes YAML files - understand each resource step by step.

## 📁 Files Explained

| File | What It Does | Why Needed |
|------|--------------|------------|
| `00-namespace.yaml` | Creates isolated namespace | Organizes resources |
| `01-configmap.yaml` | JupyterHub configuration | Authentication, spawner settings, GPU |
| `02-secrets.yaml` | Proxy token, credentials | Security |
| `03-pvc.yaml` | Hub database storage | Persists JupyterHub data |
| `04-serviceaccount.yaml` | RBAC permissions | Lets Hub create user pods |
| `05-hub-deployment.yaml` | Hub pod (brain) | Manages users, spawns notebooks |
| `06-hub-service.yaml` | Hub network service | Internal communication |
| `07-proxy-deployment.yaml` | Proxy pod (router) | Routes traffic to notebooks |
| `08-proxy-service.yaml` | Proxy network service | **Cloudflare connects here** |
| `setup-gpu-timeslicing.sh` | Enable GPU sharing | **Run first for multi-user GPU!** |
| `GPU-SHARING.md` | GPU sharing guide | Multi-user configuration |

## 🎮 GPU Sharing (IMPORTANT!)

**By default:** 1 GPU = 1 user (others wait)  
**With time-slicing:** 1 GPU = 4 users simultaneously!

### Enable Multi-User GPU Access

```bash
# Run BEFORE deploying JupyterHub
cd k8s-manifests
./setup-gpu-timeslicing.sh
```

This converts your 1 RTX 5090 → 4 virtual GPUs (4 concurrent users).

**See:** `GPU-SHARING.md` for details.

## 🚀 Deploy (Manual - One by One)

### Step 1: Generate Secret Token

```bash
openssl rand -hex 32
```

Copy output and update `02-secrets.yaml` line 11.

### Step 2: Configure Azure AD

Edit `01-configmap.yaml` lines 44-47 with your Azure AD credentials.

### Step 3: Apply Resources in Order

```bash
# Create namespace
kubectl apply -f k8s-manifests/00-namespace.yaml

# Create configuration
kubectl apply -f k8s-manifests/01-configmap.yaml

# Create secrets (AFTER updating proxy-token!)
kubectl apply -f k8s-manifests/02-secrets.yaml

# Create storage
kubectl apply -f k8s-manifests/03-pvc.yaml

# Create permissions
kubectl apply -f k8s-manifests/04-serviceaccount.yaml

# Deploy Hub
kubectl apply -f k8s-manifests/05-hub-deployment.yaml
kubectl apply -f k8s-manifests/06-hub-service.yaml

# Deploy Proxy
kubectl apply -f k8s-manifests/07-proxy-deployment.yaml
kubectl apply -f k8s-manifests/08-proxy-service.yaml
```

### Step 4: Verify

```bash
kubectl get pods -n jupyterhub-test
# Should see: hub and proxy pods Running

kubectl get svc -n jupyterhub-test
# Should see: hub and proxy-public services
```

### Step 5: Access

Cloudflare tunnel → `http://localhost:80` → proxy-public service → JupyterHub

## 🚀 Deploy (Quick - All at Once)

```bash
kubectl apply -f k8s-manifests/
```

**Note:** Make sure you updated secrets first!

## 🎮 GPU Configuration

GPU is **enabled** in `01-configmap.yaml`:

```python
# Lines 24-25:
c.KubeSpawner.extra_resource_limits = {"nvidia.com/gpu": "1"}
c.KubeSpawner.extra_resource_guarantees = {"nvidia.com/gpu": "1"}
```

To disable GPU, comment out those lines.

## 🔄 Updates

### Update JupyterHub Configuration

```bash
# Edit configmap
nano k8s-manifests/01-configmap.yaml

# Apply changes
kubectl apply -f k8s-manifests/01-configmap.yaml

# Restart hub to use new config
kubectl rollout restart deployment/hub -n jupyterhub-test
```

### Update Notebook Image

```bash
# Edit configmap line 13
c.KubeSpawner.image = 'docker.io/ermircjapi/jupyterhub-notebook:v2'

# Apply
kubectl apply -f k8s-manifests/01-configmap.yaml
kubectl rollout restart deployment/hub -n jupyterhub-test
```

## 🗑️ Uninstall

```bash
# Delete all resources
kubectl delete -f k8s-manifests/

# Or delete namespace (removes everything)
kubectl delete namespace jupyterhub-test
```

## 🆚 vs Helm Deployment

### K8s Manifests (This Approach)
**Pros:**
- ✅ See every resource clearly
- ✅ Understand what each does
- ✅ Full control
- ✅ Learn Kubernetes step by step

**Cons:**
- ❌ More files to manage
- ❌ Manual updates
- ❌ More complex

### Helm (Alternative - `infra/jupyterhub/values-v1.yaml`)
**Pros:**
- ✅ One command deployment
- ✅ One file configuration
- ✅ Easier updates
- ✅ Helm manages everything

**Cons:**
- ❌ Less visible what's created
- ❌ "Magic" under the hood

## 💡 Recommendation

**Learning?** Use K8s manifests (this directory)
**Production?** Use Helm (`./scripts/deploy_jhub_v1.sh`)

Both create the same result - choose what works for you!

## 🔍 Understanding Each Resource

### Namespace
Isolated environment for JupyterHub - like a separate apartment.

### ConfigMap
Configuration file - contains Python code that configures:
- How to spawn user notebooks (KubeSpawner)
- GPU allocation
- Resource limits
- Authentication (Azure AD)

### Secrets
Sensitive data:
- Proxy token (hub and proxy must share this)
- Azure AD credentials (optional)

### PVC (Persistent Volume Claim)
Storage for Hub's SQLite database - persists user data.

### ServiceAccount + RBAC
Permissions - lets Hub create pods/PVCs for users.

### Hub Deployment
The pod that runs JupyterHub Hub - the brain.
- Handles authentication
- Spawns user notebooks
- Manages sessions

### Hub Service
Network endpoint for Hub - allows proxy to reach it.

### Proxy Deployment
The pod that runs the proxy - the router.
- Routes `/` to Hub
- Routes `/user/alice/` to Alice's notebook
- Routes `/user/bob/` to Bob's notebook

### Proxy Service
**This is where Cloudflare connects!**
- External access point
- Port 80 → Proxy pod port 8000
- Routes all traffic

## 🌊 Traffic Flow

```
User Browser
    ↓
Cloudflare (https://jupyterhub.ccrolabs.com)
    ↓
Cloudflare Tunnel
    ↓
k3s Traefik (localhost:80)
    ↓
proxy-public Service (port 80)
    ↓
Proxy Pod (port 8000)
    ↓
├─ /hub/* → Hub Pod → Authentication, Dashboard
└─ /user/alice/* → Alice's Notebook Pod
```

## ✅ Checklist

Before deploying:
- [ ] Generated proxy token: `openssl rand -hex 32`
- [ ] Updated `02-secrets.yaml` with token
- [ ] Updated `01-configmap.yaml` with Azure AD credentials
- [ ] Updated admin email in configmap
- [ ] Built and pushed notebook image to Docker Hub
- [ ] Cloudflare tunnel is running and pointed to localhost:80

Then deploy!

