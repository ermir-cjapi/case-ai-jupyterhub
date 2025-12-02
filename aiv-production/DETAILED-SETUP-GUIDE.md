# Detailed Setup Guide – JupyterHub on NVIDIA Kubernetes

This guide walks you through setting up a production-like JupyterHub environment on your on-premises NVIDIA Kubernetes cluster, preparing you for the eventual AIV production deployment.

## Table of Contents

1. [Prerequisites Check](#1-prerequisites-check)
2. [Initial Configuration](#2-initial-configuration)
3. [Build and Push Base Notebook Image](#3-build-and-push-base-notebook-image)
4. [Prepare Kubernetes Infrastructure](#4-prepare-kubernetes-infrastructure)
5. [SSL/TLS Certificate Setup (Detailed)](#5-ssltls-certificate-setup-detailed)
6. [Configure Multi-User Authentication](#6-configure-multi-user-authentication)
7. [Deploy JupyterHub](#7-deploy-jupyterhub)
8. [Test Multi-User Access](#8-test-multi-user-access)
9. [GitHub Integration for CI/CD](#9-github-integration-for-cicd)
10. [GitHub OAuth Authentication (Optional)](#10-github-oauth-authentication-optional)
11. [Monitoring Setup](#11-monitoring-setup)
12. [GPU Testing](#12-gpu-testing)
13. [Backup and Maintenance](#13-backup-and-maintenance)
14. [Preparing for AIV Production](#14-preparing-for-aiv-production)

---

## 1. Prerequisites Check

### 1.1 Kubernetes Cluster Verification

Check that your cluster is operational:

```bash
# Verify kubectl works
kubectl cluster-info
kubectl get nodes

# Check node labels and GPU availability
kubectl get nodes -o wide
kubectl describe nodes | grep -i gpu
```

### 1.2 GPU Driver and Device Plugin

Verify NVIDIA drivers and device plugin:

```bash
# Check NVIDIA driver on GPU nodes (SSH to a GPU node)
nvidia-smi

# Back on your admin machine, check for the NVIDIA device plugin
kubectl get daemonset -A | grep nvidia
kubectl get nodes -o json | jq '.items[].status.capacity'
```

You should see `nvidia.com/gpu: "X"` where X is the number of GPUs.

If the device plugin is missing, install it:

```bash
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

### 1.3 Storage Class

Check available storage classes:

```bash
kubectl get storageclass

# Note the default storage class (marked with "(default)")
# Common names: standard, local-path, nfs-client, ceph-rbd
```

**Record your storage class name** – you'll need it later. For this guide, we'll use `local-path` as an example.

### 1.4 Ingress Controller

Check if an ingress controller is installed:

```bash
kubectl get pods -A | grep ingress
```

If you don't have one, install **ingress-nginx**:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

Get the ingress external IP:

```bash
kubectl get svc -n ingress-nginx
```

### 1.5 DNS Setup

You need a DNS name pointing to your ingress controller. Options:

**Option A: Internal DNS**
- Add an A record in your corporate DNS: `jupyterhub.lab.yourcompany.local` → ingress IP

**Option B: /etc/hosts (testing only)**
- On your laptop: `sudo nano /etc/hosts`
- Add: `<INGRESS_IP> jupyterhub.lab.local`

**For this guide, we'll use:** `jupyterhub.lab.local`

### 1.6 Container Registry Access

You need a registry for your notebook images. Options:

- **GitHub Container Registry (ghcr.io)** – Free for public/private repos
- **Docker Hub** – `docker.io/your-username`
- **Harbor** or other private registry

**For this guide, we'll use GitHub Container Registry:**

```bash
# Create a GitHub Personal Access Token (PAT)
# Go to: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Generate new token with scopes: write:packages, read:packages, delete:packages

# Log in to GitHub Container Registry
echo "YOUR_GITHUB_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

---

## 2. Initial Configuration

### 2.1 Clone the Repository

```bash
git clone https://github.com/your-org/iav-jupyterhub.git
cd iav-jupyterhub
```

### 2.2 Set Environment Variables

Create a file `lab-config.env` to store your settings:

```bash
# lab-config.env
export REGISTRY="ghcr.io/YOUR_GITHUB_USERNAME"
export IMAGE_NAME="iav/base-notebook"
export IMAGE_TAG="v1"
export JHUB_NAMESPACE="jupyterhub-test"
export JHUB_HOST="jupyterhub.lab.local"
export STORAGE_CLASS="local-path"
```

Load it:

```bash
source lab-config.env
```

---

## 3. Build and Push Base Notebook Image

### 3.1 Customize the Dockerfile (Optional)

Edit `images/base-notebook/Dockerfile` to add GPU libraries:

```dockerfile
# Add after line 23 (before ENV JUPYTER_ENABLE_LAB):

# GPU support - PyTorch with CUDA 12.1
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# TensorFlow with GPU support
RUN pip install --no-cache-dir tensorflow[and-cuda]

# Additional ML tools
RUN pip install --no-cache-dir \
    transformers \
    datasets \
    jupyterlab-git
```

### 3.2 Build and Push

```bash
# Ensure environment variables are set
source lab-config.env

# Build and push
./scripts/build_base_image.sh
```

This will:
- Build the Docker image
- Tag it as `ghcr.io/YOUR_GITHUB_USERNAME/iav/base-notebook:v1`
- Push to GitHub Container Registry

### 3.3 Verify the Image

```bash
docker images | grep base-notebook

# Test locally (optional)
docker run -it --rm ghcr.io/YOUR_GITHUB_USERNAME/iav/base-notebook:v1 python -c "import torch; print(torch.cuda.is_available())"
```

---

## 4. Prepare Kubernetes Infrastructure

### 4.1 Update Storage Class in Manifests

Edit `infra/storage/pvc-home.yaml`:

```yaml
spec:
  storageClassName: local-path  # Change to your storage class
```

### 4.2 Update Namespace Settings (Optional)

If you want a different namespace, edit `infra/namespaces.yaml` and change `jupyterhub-test` to your preferred name.

### 4.3 Apply Infrastructure Manifests

```bash
# Create namespace and RBAC
kubectl apply -f infra/namespaces.yaml

# Create shared storage
kubectl apply -f infra/storage/pvc-home.yaml

# Verify PVC is created and bound
kubectl get pvc -n ${JHUB_NAMESPACE}
```

---

## 5. SSL/TLS Certificate Setup (Detailed)

This is a critical section. You have three main options:

### Option A: Self-Signed Certificate (Simplest, for Lab Only)

**Step 1: Generate the certificate**

```bash
# Create a directory for certs
mkdir -p certs
cd certs

# Generate private key and certificate
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout jhub.key \
  -out jhub.crt \
  -subj "/C=US/ST=State/L=City/O=YourOrg/CN=${JHUB_HOST}"

# View the certificate
openssl x509 -in jhub.crt -text -noout
```

**Step 2: Create Kubernetes TLS secret**

```bash
kubectl -n ${JHUB_NAMESPACE} create secret tls jupyterhub-tls \
  --cert=jhub.crt \
  --key=jhub.key

# Verify secret
kubectl -n ${JHUB_NAMESPACE} get secret jupyterhub-tls
```

**Step 3: Trust the certificate in your browser**

For testing only:
- Chrome/Edge: When you visit the site, click "Advanced" → "Proceed to jupyterhub.lab.local (unsafe)"
- Firefox: Click "Advanced" → "Accept the Risk and Continue"

For a better experience, import the certificate:

**On Windows:**
```powershell
# Import the certificate to Trusted Root Certification Authorities
certutil -addstore -enterprise -f "Root" certs\jhub.crt
```

**On Linux/Mac:**
```bash
# Chrome/Chromium uses system certs
sudo cp certs/jhub.crt /usr/local/share/ca-certificates/jupyterhub.crt
sudo update-ca-certificates

# Firefox uses its own cert store - import via Settings → Privacy & Security → Certificates → View Certificates → Import
```

### Option B: Let's Encrypt with cert-manager (Public Access)

Only if your cluster is accessible from the internet.

**Step 1: Install cert-manager**

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
```

**Step 2: Create a ClusterIssuer**

Create `certs/letsencrypt-issuer.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    email: your-email@example.com  # CHANGE THIS
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

Apply it:

```bash
kubectl apply -f certs/letsencrypt-issuer.yaml
```

**Step 3: Create a Certificate**

Create `certs/jupyterhub-cert.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: jupyterhub-cert
  namespace: jupyterhub-test  # Change if using different namespace
spec:
  secretName: jupyterhub-tls
  issuerRef:
    kind: ClusterIssuer
    name: letsencrypt-prod
  dnsNames:
    - jupyterhub.lab.local  # CHANGE to your actual public DNS
```

Apply it:

```bash
kubectl apply -f certs/jupyterhub-cert.yaml

# Watch certificate issuance
kubectl describe certificate jupyterhub-cert -n ${JHUB_NAMESPACE}
kubectl get certificaterequest -n ${JHUB_NAMESPACE}
```

The certificate will be automatically placed in the `jupyterhub-tls` secret.

### Option C: Corporate/Internal CA Certificate

If your organization has an internal Certificate Authority:

**Step 1: Request certificate from your CA**

- Request a certificate for `jupyterhub.lab.local` from your IT/security team
- You'll receive: `server.crt` and `server.key`

**Step 2: Create the Kubernetes secret**

```bash
kubectl -n ${JHUB_NAMESPACE} create secret tls jupyterhub-tls \
  --cert=server.crt \
  --key=server.key
```

Since your corporate CA is already trusted by company machines, browsers will automatically trust this certificate.

### 5.4 Update Ingress with Your Hostname

Edit `infra/network/ingress.yaml`:

```yaml
spec:
  tls:
    - hosts:
        - jupyterhub.lab.local  # Your DNS name
      secretName: jupyterhub-tls
  rules:
    - host: jupyterhub.lab.local  # Your DNS name
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: proxy-public
                port:
                  number: 80
```

---

## 6. Configure Multi-User Authentication

You have three options for simulating multi-user access without Azure AD:

### Option A: DummyAuthenticator (Simplest Multi-User Simulation)

**Already configured in `infra/jupyterhub/values-v1.yaml`**

This allows ANY username with the shared password. Perfect for testing multi-user scenarios.

Edit `infra/jupyterhub/values-v1.yaml`:

```yaml
hub:
  extraConfig:
    00-local-auth: |
      from jupyterhub.auth import DummyAuthenticator
      c.JupyterHub.authenticator_class = DummyAuthenticator
      c.DummyAuthenticator.password = "TestPass123!"  # CHANGE THIS
      c.Authenticator.admin_users = {"admin", "your-username"}
```

**How it works:**
- User logs in with username `alice` and password `TestPass123!` → gets a pod named `jupyter-alice`
- User logs in with username `bob` and password `TestPass123!` → gets a pod named `jupyter-bob`
- Each user has separate storage and resources

### Option B: NativeAuthenticator (Per-User Passwords)

For more realistic user management without external auth.

**Step 1: Update values file**

Edit `infra/jupyterhub/values-v1.yaml` and replace the `00-local-auth` section:

```yaml
hub:
  extraConfig:
    00-native-auth: |
      from nativeauthenticator import NativeAuthenticator
      c.JupyterHub.authenticator_class = NativeAuthenticator
      c.Authenticator.admin_users = {"admin"}
      c.NativeAuthenticator.open_signup = False  # Admins must authorize users
      c.NativeAuthenticator.minimum_password_length = 10
      c.NativeAuthenticator.check_common_password = True
      c.NativeAuthenticator.allowed_failed_logins = 3
      c.NativeAuthenticator.seconds_before_next_try = 600
```

**Step 2: Ensure the hub image has nativeauthenticator**

The default JupyterHub hub image may not include it. You can:

1. Add to hub configuration:

```yaml
hub:
  extraConfig:
    00-install-native: |
      import subprocess
      import sys
      subprocess.check_call([sys.executable, "-m", "pip", "install", "jupyterhub-nativeauthenticator"])
    01-native-auth: |
      from nativeauthenticator import NativeAuthenticator
      # ... rest of config
```

Or build a custom hub image (more advanced).

**Step 3: After deployment, manage users**

1. First user signs up at `/hub/signup`
2. Admin logs in and goes to `/hub/authorize` to approve users
3. Users can then log in with their individual passwords

### Option C: GitHub OAuth (Most Realistic)

See section [10. GitHub OAuth Authentication](#10-github-oauth-authentication-optional) below.

**Recommendation:** Start with **DummyAuthenticator** for your first deployment, then switch to GitHub OAuth once basics work.

---

## 7. Deploy JupyterHub

### 7.1 Update JupyterHub Values with Your Settings

Edit `infra/jupyterhub/values-v1.yaml`:

```yaml
proxy:
  secretToken: "GENERATE_A_RANDOM_64_CHAR_HEX_STRING"  # See below
  service:
    type: ClusterIP
  https:
    enabled: false  # We handle TLS at ingress

hub:
  service:
    type: ClusterIP
  db:
    type: sqlite-pvc
  config:
    JupyterHub:
      admin_access: true
  extraConfig:
    00-local-auth: |
      from jupyterhub.auth import DummyAuthenticator
      c.JupyterHub.authenticator_class = DummyAuthenticator
      c.DummyAuthenticator.password = "TestPass123!"  # CHANGE THIS
      c.Authenticator.admin_users = {"admin"}

singleuser:
  image:
    name: ghcr.io/YOUR_GITHUB_USERNAME/iav/base-notebook  # YOUR REGISTRY
    tag: v1
    pullPolicy: IfNotPresent
  storage:
    type: dynamic
    capacity: 10Gi
    dynamic:
      storageClass: local-path  # YOUR STORAGE CLASS
    extraVolumes:
      - name: shared-home
        persistentVolumeClaim:
          claimName: jupyterhub-shared-home
    extraVolumeMounts:
      - name: shared-home
        mountPath: /shared
  cpu:
    limit: 2
    guarantee: 0.5
  memory:
    limit: 4G
    guarantee: 1G
  # Uncomment for GPU access:
  # extraResource:
  #   limits:
  #     nvidia.com/gpu: "1"
  defaultUrl: /lab

cull:
  enabled: true
  timeout: 3600
  every: 600

prePuller:
  continuous:
    enabled: true
```

**Generate a secure proxy token:**

```bash
openssl rand -hex 32
```

Copy the output and paste it as `proxy.secretToken` value.

### 7.2 Run the Deployment Script

```bash
# Ensure environment is set
source lab-config.env

# Deploy
./scripts/deploy_jhub_v1.sh
```

This script will:
1. Create namespace if missing
2. Apply base manifests
3. Add JupyterHub Helm repo
4. Install/upgrade the Helm release
5. Apply ingress and monitoring

### 7.3 Monitor Deployment

```bash
# Watch pods come up
kubectl get pods -n ${JHUB_NAMESPACE} -w

# Check logs if something fails
kubectl logs -n ${JHUB_NAMESPACE} -l app=jupyterhub -l component=hub --tail=50
```

Wait until all pods show `Running` and `Ready 1/1`.

---

## 8. Test Multi-User Access

### 8.1 Run Smoke Test

```bash
export INGRESS_HOST="${JHUB_HOST}"
./scripts/smoke_test_v1.sh
```

### 8.2 Access JupyterHub UI

Open your browser:

```
https://jupyterhub.lab.local
```

You may need to accept the self-signed certificate warning.

### 8.3 Log In as First User

- **Username:** `admin`
- **Password:** `TestPass123!` (or whatever you set)

You should:
1. See the JupyterHub spawn page
2. Click "Start My Server"
3. Wait ~30-60 seconds for your pod to start
4. Land in JupyterLab

### 8.4 Test Multi-User by Creating Additional Sessions

**Option 1: Incognito/Private Windows**

Open an incognito window and log in as a different user:

- **Username:** `alice`
- **Password:** `TestPass123!`

**Option 2: Different Browsers**

Use Chrome for one user, Firefox for another.

**Verify multi-user isolation:**

```bash
# On your admin machine
kubectl get pods -n ${JHUB_NAMESPACE}

# You should see:
# jupyter-admin-...
# jupyter-alice-...
```

Each user should have:
- Their own pod
- Their own home directory
- Isolated resources

### 8.5 Test Shared Storage

In one user's notebook (e.g., `admin`):

```python
# Create a file in shared directory
with open('/shared/test.txt', 'w') as f:
    f.write('Hello from admin')
```

In another user's notebook (e.g., `alice`):

```python
# Read the file
with open('/shared/test.txt', 'r') as f:
    print(f.read())  # Should print: Hello from admin
```

---

## 9. GitHub Integration for CI/CD

### 9.1 Create GitHub Actions Workflow for Image Build

Create `.github/workflows/build-image.yml`:

```yaml
name: Build Base Notebook Image

on:
  push:
    branches: [ main ]
    paths:
      - 'images/base-notebook/**'
      - '.github/workflows/build-image.yml'
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/iav/base-notebook

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value=v1

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./images/base-notebook
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 9.2 Create GitHub Actions Workflow for Deployment (Optional)

Create `.github/workflows/deploy-jhub.yml`:

```yaml
name: Deploy JupyterHub

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        type: choice
        options:
          - lab
          - aiv-prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubectl
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Set environment variables
        run: |
          if [ "${{ github.event.inputs.environment }}" = "lab" ]; then
            echo "NAMESPACE=jupyterhub-test" >> $GITHUB_ENV
            echo "VALUES_FILE=infra/jupyterhub/values-v1.yaml" >> $GITHUB_ENV
          else
            echo "NAMESPACE=jupyterhub-prod" >> $GITHUB_ENV
            echo "VALUES_FILE=infra/jupyterhub/values-aiv-prod.yaml" >> $GITHUB_ENV
          fi

      - name: Install Helm
        uses: azure/setup-helm@v3

      - name: Deploy JupyterHub
        run: |
          export NAMESPACE=${{ env.NAMESPACE }}
          export VALUES_FILE=${{ env.VALUES_FILE }}
          ./scripts/deploy_jhub_v1.sh
```

**To use this workflow:**

1. Add your kubeconfig as a GitHub secret:

```bash
# Base64 encode your kubeconfig
cat ~/.kube/config | base64 -w 0

# Go to GitHub repo → Settings → Secrets and variables → Actions → New repository secret
# Name: KUBECONFIG
# Value: <paste the base64 string>
```

2. Trigger manually via Actions tab → Deploy JupyterHub → Run workflow

### 9.3 Commit and Push

```bash
git add .github/workflows/
git commit -m "Add GitHub Actions CI/CD workflows"
git push origin main
```

Check the **Actions** tab in GitHub to see the build running.

---

## 10. GitHub OAuth Authentication (Optional)

### 10.1 Create GitHub OAuth App

1. Go to GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**

2. Fill in:
   - **Application name:** `JupyterHub Lab`
   - **Homepage URL:** `https://jupyterhub.lab.local`
   - **Authorization callback URL:** `https://jupyterhub.lab.local/hub/oauth_callback`

3. Click **Register application**

4. **Note the Client ID**

5. Click **Generate a new client secret** and **note the secret** (you won't see it again)

### 10.2 Update JupyterHub Values

Edit `infra/jupyterhub/values-v1.yaml`:

**Comment out** the DummyAuthenticator section and add GitHub OAuth:

```yaml
hub:
  extraConfig:
    # 00-local-auth: |
    #   from jupyterhub.auth import DummyAuthenticator
    #   c.JupyterHub.authenticator_class = DummyAuthenticator
    #   c.DummyAuthenticator.password = "TestPass123!"
    #   c.Authenticator.admin_users = {"admin"}

    10-github-auth: |
      from oauthenticator.github import GitHubOAuthenticator
      c.JupyterHub.authenticator_class = GitHubOAuthenticator
      
      c.GitHubOAuthenticator.client_id = "YOUR_GITHUB_CLIENT_ID"
      c.GitHubOAuthenticator.client_secret = "YOUR_GITHUB_CLIENT_SECRET"
      c.GitHubOAuthenticator.oauth_callback_url = "https://jupyterhub.lab.local/hub/oauth_callback"
      
      # Optional: restrict to your organization
      # c.GitHubOAuthenticator.allowed_organizations = {"your-org-name"}
      
      # Admins by GitHub username
      c.Authenticator.admin_users = {"your-github-username"}
      
      # Optional: allow all GitHub users or specific ones
      # c.Authenticator.allow_all = True
      # c.Authenticator.allowed_users = {"user1", "user2"}
```

### 10.3 Redeploy

```bash
./scripts/deploy_jhub_v1.sh
```

### 10.4 Test GitHub OAuth

1. Visit `https://jupyterhub.lab.local`
2. You'll be redirected to GitHub
3. Authorize the app
4. You'll be redirected back and logged in

**Multi-user testing:**
- Have colleagues log in with their GitHub accounts
- Each will get their own pod and storage

---

## 11. Monitoring Setup

### 11.1 Install Prometheus and Grafana (if not present)

**Option A: Using kube-prometheus-stack (recommended)**

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

**Option B: Minimal Prometheus + Grafana**

```bash
# Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace

# Grafana
helm install grafana grafana/grafana \
  --namespace monitoring
```

### 11.2 Apply ServiceMonitor

```bash
kubectl apply -f infra/monitoring/servicemonitor.yaml
```

Verify:

```bash
kubectl get servicemonitor -n ${JHUB_NAMESPACE}
```

### 11.3 Import Grafana Dashboard

1. Get Grafana admin password:

```bash
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d
echo
```

2. Port-forward to Grafana:

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

3. Open browser: `http://localhost:3000`
   - Username: `admin`
   - Password: (from step 1)

4. Import dashboard:
   - Click **+** → **Import**
   - Upload `infra/monitoring/grafana-dashboard-v1.json`
   - Select Prometheus data source
   - Click **Import**

You should now see:
- Active users
- CPU usage per user pod
- Memory usage per user pod

---

## 12. GPU Testing

### 12.1 Enable GPU in JupyterHub

Edit `infra/jupyterhub/values-v1.yaml`:

```yaml
singleuser:
  extraResource:
    limits:
      nvidia.com/gpu: "1"
```

Redeploy:

```bash
./scripts/deploy_jhub_v1.sh
```

### 12.2 Test GPU in Notebook

Log in and create a new notebook. Run:

**Test 1: PyTorch CUDA**

```python
import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")

if torch.cuda.is_available():
    print(f"GPU device: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Simple GPU test
    x = torch.rand(1000, 1000).cuda()
    y = torch.rand(1000, 1000).cuda()
    z = torch.matmul(x, y)
    print(f"Matrix multiplication result shape: {z.shape}")
```

**Test 2: TensorFlow CUDA**

```python
import tensorflow as tf

print(f"TensorFlow version: {tf.__version__}")
print(f"GPUs available: {tf.config.list_physical_devices('GPU')}")

if tf.config.list_physical_devices('GPU'):
    # Simple test
    with tf.device('/GPU:0'):
        a = tf.random.normal([1000, 1000])
        b = tf.random.normal([1000, 1000])
        c = tf.matmul(a, b)
    print(f"Matrix multiplication result shape: {c.shape}")
```

**Test 3: nvidia-smi from notebook terminal**

Open a terminal in JupyterLab and run:

```bash
nvidia-smi
```

You should see your GPU listed.

### 12.3 GPU Profiles (Optional)

For different user tiers (CPU-only vs GPU), edit `values-v1.yaml`:

```yaml
singleuser:
  profileList:
    - display_name: "CPU Only - Small"
      description: "2 CPU cores, 4GB RAM"
      default: true
      kubespawner_override:
        cpu_limit: 2
        cpu_guarantee: 0.5
        mem_limit: "4G"
        mem_guarantee: "1G"
    
    - display_name: "GPU - Standard"
      description: "4 CPU cores, 16GB RAM, 1 GPU"
      kubespawner_override:
        cpu_limit: 4
        cpu_guarantee: 1
        mem_limit: "16G"
        mem_guarantee: "4G"
        extra_resource_limits:
          nvidia.com/gpu: "1"
    
    - display_name: "GPU - Large"
      description: "8 CPU cores, 32GB RAM, 2 GPUs"
      kubespawner_override:
        cpu_limit: 8
        cpu_guarantee: 2
        mem_limit: "32G"
        mem_guarantee: "8G"
        extra_resource_limits:
          nvidia.com/gpu: "2"
```

After redeploying, users will see a dropdown to choose their server size.

---

## 13. Backup and Maintenance

### 13.1 Backup User Home Directories

Create a backup script `scripts/backup_user_data.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-jupyterhub-test}"
BACKUP_DIR="${BACKUP_DIR:-./backups/$(date +%Y%m%d-%H%M%S)}"

mkdir -p "${BACKUP_DIR}"

echo "Backing up PVCs in namespace ${NAMESPACE}..."

for pvc in $(kubectl get pvc -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}'); do
  echo "Backing up PVC: ${pvc}"
  
  # Create a temporary pod to access the PVC
  kubectl run -n "${NAMESPACE}" backup-pod-${pvc} \
    --image=busybox \
    --restart=Never \
    --overrides="{
      \"spec\": {
        \"containers\": [{
          \"name\": \"backup\",
          \"image\": \"busybox\",
          \"command\": [\"sleep\", \"3600\"],
          \"volumeMounts\": [{
            \"name\": \"data\",
            \"mountPath\": \"/data\"
          }]
        }],
        \"volumes\": [{
          \"name\": \"data\",
          \"persistentVolumeClaim\": {
            \"claimName\": \"${pvc}\"
          }
        }]
      }
    }"
  
  # Wait for pod to be ready
  kubectl wait -n "${NAMESPACE}" --for=condition=Ready pod/backup-pod-${pvc} --timeout=60s
  
  # Tar and copy data
  kubectl exec -n "${NAMESPACE}" backup-pod-${pvc} -- tar czf /tmp/${pvc}.tar.gz -C /data .
  kubectl cp "${NAMESPACE}/backup-pod-${pvc}:/tmp/${pvc}.tar.gz" "${BACKUP_DIR}/${pvc}.tar.gz"
  
  # Cleanup
  kubectl delete -n "${NAMESPACE}" pod backup-pod-${pvc}
  
  echo "Backed up ${pvc} to ${BACKUP_DIR}/${pvc}.tar.gz"
done

echo "Backup complete: ${BACKUP_DIR}"
```

Make it executable:

```bash
chmod +x scripts/backup_user_data.sh
```

Run backups:

```bash
./scripts/backup_user_data.sh
```

### 13.2 Update JupyterHub

To update to a new chart version:

```bash
# Check current version
helm list -n ${JHUB_NAMESPACE}

# See available versions
helm search repo jupyterhub/jupyterhub --versions

# Update to specific version
# Edit scripts/deploy_jhub_v1.sh and change CHART_VERSION
# Then:
./scripts/deploy_jhub_v1.sh
```

### 13.3 Clean Up Idle Resources

Culling is already enabled in the config (1 hour idle timeout). To manually clean up:

```bash
# List all user pods
kubectl get pods -n ${JHUB_NAMESPACE} -l component=singleuser-server

# Delete a specific user's pod (they can restart it)
kubectl delete pod -n ${JHUB_NAMESPACE} jupyter-<username>
```

---

## 14. Preparing for AIV Production

### 14.1 Document Environment-Specific Settings

Create a checklist file `AIV-MIGRATION-CHECKLIST.md`:

```markdown
# AIV Production Migration Checklist

## Environment Differences

| Setting | Lab | AIV Production |
|---------|-----|----------------|
| Registry | ghcr.io/your-user | registry.aiv.internal |
| Namespace | jupyterhub-test | jupyterhub-prod |
| Storage Class | local-path | ceph-rbd |
| Ingress Host | jupyterhub.lab.local | jupyterhub.aiv.internal |
| TLS Method | Self-signed | Corporate CA |
| Auth | GitHub OAuth | Entra ID |
| GitLab URL | github.com | gitlab.aiv.internal |
| Monitoring | Local Prometheus | AIV Grafana/Prometheus stack |

## Pre-Migration Tasks

- [ ] Test backup and restore procedures
- [ ] Document all customizations in Dockerfile
- [ ] Verify GPU allocation policies
- [ ] Test Entra ID auth with AIV tenant (dev environment)
- [ ] Align resource quotas with AIV capacity planning
- [ ] Review and update user guide for AIV users
- [ ] Set up CI/CD in AIV GitLab instance
- [ ] Coordinate with AIV IT for:
  - [ ] Entra ID app registration
  - [ ] TLS certificate issuance
  - [ ] Storage provisioning (Ceph/S3)
  - [ ] Network policies and firewall rules
  - [ ] Monitoring integration

## Migration Steps

1. Create `infra/jupyterhub/values-aiv-prod.yaml` based on `values-v1.yaml`
2. Update all AIV-specific values
3. Test in AIV staging/dev environment first
4. Schedule production deployment with AIV team
5. Run smoke tests in AIV environment
6. Monitor for 48 hours
7. Hand off to AIV ops team
```

### 14.2 Create AIV-Specific Values File

Copy and customize:

```bash
cp infra/jupyterhub/values-v1.yaml infra/jupyterhub/values-aiv-prod.yaml
```

Edit `values-aiv-prod.yaml` to switch to Entra ID:

```yaml
hub:
  extraConfig:
    # Comment out GitHub/Dummy auth
    10-entra-id-auth: |
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      
      c.AzureAdOAuthenticator.tenant_id = "AIV_TENANT_ID"
      c.AzureAdOAuthenticator.client_id = "AIV_CLIENT_ID"
      c.AzureAdOAuthenticator.client_secret = "AIV_CLIENT_SECRET"
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.aiv.internal/hub/oauth_callback"
      
      # Map Entra groups to admin
      c.AzureAdOAuthenticator.admin_groups = {"jupyterhub-admins"}
      c.AzureAdOAuthenticator.allowed_groups = {"jupyterhub-users"}

singleuser:
  image:
    name: registry.aiv.internal/ml-platform/base-notebook
    tag: v1
  storage:
    dynamic:
      storageClass: ceph-rbd  # AIV storage class
```

### 14.3 Test in Your Lab with Your Entra ID

If you have access to a test Entra ID tenant:

1. Register an app in your Entra ID (using lab callback URL)
2. Update `values-v1.yaml` with Entra auth (comment out section currently there, uncomment Entra example)
3. Redeploy and test
4. Document any issues for AIV team

---

## Troubleshooting

### Pods Not Starting

```bash
kubectl get pods -n ${JHUB_NAMESPACE}
kubectl describe pod <pod-name> -n ${JHUB_NAMESPACE}
kubectl logs <pod-name> -n ${JHUB_NAMESPACE}
```

Common issues:
- Image pull errors: Check registry authentication
- Storage not binding: Check PVC status and storage class
- GPU not available: Check node labels and device plugin

### Ingress Not Working

```bash
kubectl get ingress -n ${JHUB_NAMESPACE}
kubectl describe ingress jupyterhub -n ${JHUB_NAMESPACE}

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

### Authentication Failing

```bash
# Check hub logs
kubectl logs -n ${JHUB_NAMESPACE} -l component=hub --tail=100

# Common fixes:
# - Verify callback URL matches exactly
# - Check client ID/secret
# - Ensure TLS is working (OAuth requires HTTPS)
```

### GPU Not Detected in Notebook

```bash
# Check if pod has GPU allocated
kubectl describe pod jupyter-<username> -n ${JHUB_NAMESPACE} | grep -A 5 Limits

# Check device plugin
kubectl get daemonset -A | grep nvidia

# Check node GPU capacity
kubectl get nodes -o json | jq '.items[].status.capacity'
```

---

## Next Steps

1. **Complete the initial deployment** following sections 1-7
2. **Test multi-user access** (section 8)
3. **Set up GitHub CI/CD** (section 9)
4. **Configure monitoring** (section 11)
5. **Test GPU workloads** (section 12)
6. **Document your specific configuration** for future reference
7. **Schedule regular backups** (section 13.1)
8. **Prepare for AIV migration** (section 14)

---

## Support and References

- **JupyterHub Documentation:** https://jupyterhub.readthedocs.io/
- **Zero to JupyterHub (K8s):** https://z2jh.jupyter.org/
- **OAuthenticator Docs:** https://oauthenticator.readthedocs.io/
- **NVIDIA Device Plugin:** https://github.com/NVIDIA/k8s-device-plugin
- **cert-manager:** https://cert-manager.io/docs/

For questions specific to this setup, refer to:
- `docs/admin-runbook.md` – Operations guide
- `docs/architecture.md` – Architecture overview
- `docs/user-guide.md` – End-user documentation

