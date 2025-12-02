# Repository Structure

## 📁 Directory Layout

```
case-ai-jupyterhub/
│
├── 🐳 helm/                         # Helm deployment (quick & simple)
│   ├── values-helm.yaml              # All configuration in one file
│   ├── deploy_jhub_helm.sh           # Deploy with Helm
│   ├── delete_jhub_helm.sh           # Delete Helm deployment
│   ├── smoke_test_helm.sh            # Test deployment
│   ├── setup-gpu-timeslicing.sh      # Enable multi-user GPU (4 users per GPU)
│   └── GPU-SHARING.md                # GPU sharing guide
│
├── ⚙️  k8s-manifests/                # Plain K8s YAML files (learn step-by-step)
│   ├── 00-namespace.yaml             # Namespace
│   ├── 01-configmap.yaml             # JupyterHub config (GPU, Auth)
│   ├── 02-secrets.yaml               # Secrets (proxy token)
│   ├── 03-pvc.yaml                   # Storage for Hub
│   ├── 04-serviceaccount.yaml        # RBAC permissions
│   ├── 05-hub-deployment.yaml        # Hub pod
│   ├── 06-hub-service.yaml           # Hub service
│   ├── 07-proxy-deployment.yaml      # Proxy pod
│   ├── 08-proxy-service.yaml         # Proxy service
│   ├── deploy_k8s_manifests.sh       # Deploy all manifests
│   ├── delete_k8s_manifests.sh       # Delete all resources
│   ├── setup-gpu-timeslicing.sh      # Enable multi-user GPU (4 users per GPU)
│   ├── GPU-SHARING.md                # GPU sharing guide
│   └── README.md                     # Detailed explanation
│
├── 🖼️  images/                       # Docker images
│   ├── base-notebook/
│   │   └── Dockerfile                # Custom Jupyter notebook image
│   └── build_base_image.sh           # Build and push to Docker Hub
│
├── 🧪 local-testing/                 # Local Docker Compose testing
│   ├── docker-compose.yml            # CPU-only testing
│   ├── docker-compose-gpu.yml        # GPU testing
│   ├── jupyterhub_config.py          # Config for Docker Compose
│   ├── jupyterhub_config_gpu.py      # GPU config
│   ├── Dockerfile.jupyterhub         # JupyterHub server image
│   ├── README.md                     # Local testing guide
│   ├── QUICK-START.md                # Quick start for local
│   ├── ENTRA-ID-SETUP.md             # Azure AD setup guide
│   └── WHAT-IS-JUPYTERHUB-CONFIG.md  # Config explanation
│
├── 🏢 aiv-production/                # AIV production (completely separate)
│   └── (Full separate deployment for AIV)
│
├── ⚙️  Configuration Files
│   ├── lab-config.env                # Your environment variables
│   ├── lab-config.env.template       # Template for lab-config.env
│   └── README.md                     # Main documentation (THIS IS YOUR STARTING POINT!)
│
└── 📄 Documentation
    └── STRUCTURE.md                  # This file

```

## 🎯 What Each Directory Does

### `helm/` - Quick Helm Deployment
**Use this if:** You want the fastest deployment with least complexity.

- **One file** to configure: `values-helm.yaml`
- **One command** to deploy: `./deploy_jhub_helm.sh`
- Helm automatically creates all Kubernetes resources
- Best for: Production, when you just want it to work

### `k8s-manifests/` - Plain Kubernetes YAML
**Use this if:** You want to understand every Kubernetes resource.

- **8 YAML files** - one for each resource
- See exactly what gets created (namespace, pods, services, RBAC, etc.)
- Full transparency and control
- Best for: Learning Kubernetes, understanding JupyterHub architecture

### `images/` - Custom Notebook Images
**Always needed** - builds the Docker image users run in their notebooks.

- Based on `jupyter/minimal-notebook` with GPU support
- Includes: PyTorch, TensorFlow, transformers, scikit-learn, etc.
- Pushed to your Docker Hub: `docker.io/ermircjapi/jupyterhub-notebook`

### `local-testing/` - Docker Compose Testing
**Use before deploying to Kubernetes** - test locally first!

- Test JupyterHub on your laptop/desktop
- Try different authentication methods (GitHub, Azure AD, etc.)
- No Kubernetes needed
- Best for: Testing config changes, learning JupyterHub

### `aiv-production/` - AIV Production
**Completely separate** - for AIV deployment only.

- Different domain, authentication, infrastructure
- Not used for your NVIDIA server lab deployment
- Ignore this unless deploying to AIV

## 🔧 Configuration Files

### `lab-config.env`
**YES, still used!** Sets environment variables for:

- Docker registry: `docker.io/ermircjapi`
- Image name: `jupyterhub-notebook`
- Namespace: `jupyterhub-test`
- Domain: `jupyterhub.ccrolabs.com`
- Helm values file path

**When to use:**
```bash
source lab-config.env       # Load environment variables
./images/build_base_image.sh # Uses $REGISTRY, $IMAGE_NAME, etc.
cd helm && ./deploy_jhub_helm.sh  # Uses $VALUES_FILE, $NAMESPACE, etc.
```

### `lab-config.env.template`
Template for `lab-config.env` - copy and customize.

## 🚀 Deployment Workflow

### 1. First Time Setup

```bash
# 1. Copy and configure environment
cp lab-config.env.template lab-config.env
# Edit lab-config.env with your values

# 2. Enable GPU sharing (IMPORTANT!)
# Choose helm/ or k8s-manifests/ based on your deployment method
cd helm  # or cd k8s-manifests
./setup-gpu-timeslicing.sh  # Converts 1 GPU → 4 users
cd ..

# 3. Build and push notebook image
source lab-config.env
docker login
./images/build_base_image.sh
```

### 2. Choose Deployment Method

**Option A: Helm (Recommended)**
```bash
# Edit configuration
nano helm/values-helm.yaml
# Set: proxy token, Azure AD credentials, admin users

# Deploy
cd helm
./deploy_jhub_helm.sh
```

**Option B: K8s Manifests (Learning)**
```bash
# Edit configuration
nano k8s-manifests/01-configmap.yaml  # JupyterHub config
nano k8s-manifests/02-secrets.yaml     # Proxy token

# Deploy
cd k8s-manifests
./deploy_k8s_manifests.sh
```

### 3. Access JupyterHub

**https://jupyterhub.ccrolabs.com**

(Cloudflare tunnel → k3s Traefik → JupyterHub proxy-public service)

## 🔄 Common Tasks

### Update Notebook Image
```bash
# Edit images/base-notebook/Dockerfile
# Then:
source lab-config.env
./images/build_base_image.sh

# Restart pods to use new image
kubectl rollout restart deployment/hub -n jupyterhub-test
```

### Change Authentication
**Helm:**
```bash
nano helm/values-helm.yaml  # Edit auth section
cd helm && ./deploy_jhub_helm.sh
```

**K8s Manifests:**
```bash
nano k8s-manifests/01-configmap.yaml  # Edit auth section
cd k8s-manifests && ./deploy_k8s_manifests.sh
```

### View Logs
```bash
kubectl logs -n jupyterhub-test -l component=hub -f     # Hub logs
kubectl logs -n jupyterhub-test -l component=proxy -f   # Proxy logs
kubectl get pods -n jupyterhub-test                     # All pods
```

### Delete Everything
**Helm:**
```bash
cd helm && ./delete_jhub_helm.sh
```

**K8s Manifests:**
```bash
cd k8s-manifests && ./delete_k8s_manifests.sh
```

## ❓ FAQ

### Do I need `lab-config.env`?
**YES!** It sets environment variables used by build and deployment scripts.

### Which deployment method should I use?
- **Learning Kubernetes?** → Use `k8s-manifests/`
- **Just want it working?** → Use `helm/`
- **Both work!** Choose based on your goal.

### Where is the ingress configuration?
**No ingress needed!** Cloudflare tunnel connects directly to k3s Traefik (localhost:80), which routes to JupyterHub proxy-public service.

### How do I enable GPU?
**Helm:** Edit `helm/values-helm.yaml`, uncomment GPU limits  
**K8s Manifests:** Already enabled in `k8s-manifests/01-configmap.yaml` lines 24-25

### Can I test locally first?
**YES!** Use `local-testing/` directory:
```bash
cd local-testing
docker-compose up
# Access at http://localhost:8000
```

## 📚 Documentation

- **Start here:** `README.md` (root)
- **Helm details:** `helm/values-helm.yaml` (well-commented)
- **K8s details:** `k8s-manifests/README.md`
- **Local testing:** `local-testing/README.md`
- **This file:** `STRUCTURE.md` (overview)

---

**Bottom Line:** Everything is organized by deployment method. Choose `helm/` or `k8s-manifests/`, build your image with `images/`, and optionally test locally with `local-testing/`.

