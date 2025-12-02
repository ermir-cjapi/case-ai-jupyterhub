# GPU Time-Slicing Setup - All Options Explained

You now have **4 different ways** to enable GPU time-slicing. Choose based on your preference!

## 📋 Quick Comparison

| Method | Type | Complexity | Best For |
|--------|------|------------|----------|
| **1. Shell Script** (helm/) | Automated | ⭐ Easy | Quick setup, production |
| **2. Shell Script** (k8s-manifests/) | Automated | ⭐ Easy | Quick setup, production |
| **3. Helm Chart** (NEW!) | Declarative | ⭐⭐ Medium | Helm-native workflows |
| **4. Pure K8s YAML** (NEW!) | Declarative | ⭐⭐ Medium | GitOps, learning, IaC |

---

## Option 1: Shell Script (Helm Directory)

**Location:** `helm/setup-gpu-timeslicing.sh`

### Usage
```bash
cd helm
./setup-gpu-timeslicing.sh
```

### Pros
- ✅ Fully automated (one command)
- ✅ Includes verification
- ✅ Error checking & helpful messages
- ✅ Works with Helm deployment workflow

### Cons
- ❌ Not declarative
- ❌ Harder for GitOps

### When to Use
- Quick production setup
- You're using Helm for JupyterHub deployment
- You want automatic verification

---

## Option 2: Shell Script (K8s Manifests Directory)

**Location:** `k8s-manifests/setup-gpu-timeslicing.sh`

### Usage
```bash
cd k8s-manifests
./setup-gpu-timeslicing.sh
```

### Pros/Cons
Same as Option 1, but located in k8s-manifests directory

### When to Use
- You're using K8s manifests for JupyterHub deployment
- Want script close to your deployment method

**Note:** This is identical to Option 1, just in a different location for convenience.

---

## Option 3: Helm Chart (NEW!)

**Location:** `helm/gpu-timeslicing-chart/`

### Usage
```bash
# Install with defaults (4 replicas)
helm install gpu-timeslicing helm/gpu-timeslicing-chart

# Follow instructions in output to complete setup
# (patch ClusterPolicy - shown in NOTES.txt)
```

### Customize
```bash
# 8 users per GPU
helm install gpu-timeslicing helm/gpu-timeslicing-chart --set replicas=8

# Different GPU operator namespace
helm install gpu-timeslicing helm/gpu-timeslicing-chart \
  --set gpuOperatorNamespace=nvidia-gpu-operator
```

### Pros
- ✅ Declarative (Helm-native)
- ✅ Version-controlled
- ✅ Easy to customize with `--set`
- ✅ Can include in helmfile
- ✅ Fits Helm-centric workflows

### Cons
- ⚠️ Still requires manual kubectl patch (for ClusterPolicy)
- ⚠️ Two-step process (helm install + kubectl patch)
- ❌ No automatic verification

### When to Use
- You manage everything with Helm
- Want version-controlled GPU config
- Using helmfile or similar tools
- Prefer declarative over imperative

### Files Created
```
helm/gpu-timeslicing-chart/
├── Chart.yaml                    # Helm chart metadata
├── values.yaml                   # Default values (replicas: 4)
├── templates/
│   ├── configmap.yaml            # Time-slicing ConfigMap
│   └── NOTES.txt                 # Post-install instructions
└── README.md                     # Chart documentation
```

---

## Option 4: Pure K8s YAML (NEW!)

**Location:** `k8s-manifests/gpu-timeslicing/`

### Usage
```bash
# Step 1: Apply ConfigMap
kubectl apply -f k8s-manifests/gpu-timeslicing/00-configmap.yaml

# Step 2: Patch ClusterPolicy
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config", "default": "any"}}}}'

# Step 3: Wait for restart
kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n gpu-operator

# Step 4: Verify
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

### Pros
- ✅ Fully declarative
- ✅ GitOps-friendly (ArgoCD, Flux)
- ✅ No shell scripts needed
- ✅ Infrastructure as Code
- ✅ Great for learning K8s
- ✅ Can be version-controlled

### Cons
- ❌ Multi-step manual process
- ❌ No automatic verification
- ⚠️ ClusterPolicy patch is tricky (can't use simple `kubectl apply`)

### When to Use
- GitOps workflows (ArgoCD, Flux, etc.)
- Want everything in YAML
- Learning Kubernetes internals
- Infrastructure as Code requirements
- No shell script execution allowed

### Files Created
```
k8s-manifests/gpu-timeslicing/
├── 00-configmap.yaml             # ConfigMap with time-slicing config
├── 01-patch-clusterpolicy.yaml   # Instructions (not directly applicable)
└── README.md                     # Detailed guide
```

---

## 🎯 Which One Should You Use?

### For Production (Quick Setup)
**→ Use Option 1 or 2 (Shell Script)**
- Automated
- Includes verification
- One command

### For Helm-Centric Workflows
**→ Use Option 3 (Helm Chart)**
- Fits your Helm deployment
- Easy to version
- Can use in helmfile

### For GitOps / Infrastructure as Code
**→ Use Option 4 (Pure K8s YAML)**
- Declarative
- Git-trackable
- Works with ArgoCD/Flux

### For Learning
**→ Use Option 4 (Pure K8s YAML)**
- See exactly what happens
- Understand each step
- No "magic" scripts

---

## 🔄 Can You Mix Them?

**No! Choose one method and stick with it.**

All methods create the same resources:
1. ConfigMap (`time-slicing-config`)
2. ClusterPolicy patch

Using multiple methods will conflict.

---

## 📊 Detailed Comparison

### Shell Script (Options 1 & 2)

**What it does:**
```bash
1. Creates ConfigMap via kubectl
2. Patches ClusterPolicy via kubectl
3. Waits for device plugin restart
4. Verifies GPU count changed
5. Shows detailed status
```

**Example output:**
```
✅ SUCCESS! Time-slicing is active!
   Physical GPUs: 1
   Virtual GPUs: 4
   Max concurrent users: 4
```

### Helm Chart (Option 3)

**What it does:**
```bash
1. Creates ConfigMap via Helm
2. Shows NOTES.txt with manual kubectl patch command
3. You run the kubectl patch manually
4. You verify manually
```

**Example workflow:**
```bash
helm install gpu-timeslicing ./gpu-timeslicing-chart
# Read NOTES.txt
kubectl patch clusterpolicy/cluster-policy ...  # Copy from NOTES.txt
kubectl get nodes ...  # Verify manually
```

### Pure K8s YAML (Option 4)

**What it does:**
```bash
1. You apply ConfigMap manually
2. You patch ClusterPolicy manually
3. You wait/verify manually
```

**Example workflow:**
```bash
kubectl apply -f gpu-timeslicing/00-configmap.yaml
kubectl patch clusterpolicy/cluster-policy ...
kubectl rollout status ...
kubectl get nodes ...  # Verify
```

---

## 💡 Recommendations

### Your Current Setup (1 RTX 5090, k3s, JupyterHub)

**Best choice: Shell Script (Option 1 or 2)**

Why?
- ✅ Fastest setup (1 command)
- ✅ Automatic verification
- ✅ Clear error messages
- ✅ Perfect for single-server setup

**When to switch to others:**

- If you adopt GitOps → Use Option 4 (K8s YAML)
- If you manage everything with Helm → Use Option 3 (Helm chart)
- If you want to learn internals → Use Option 4 (K8s YAML)

---

## 🎓 What You've Learned

### Key Insight: Helm Charts Have Limitations

**The official JupyterHub Helm chart cannot include GPU time-slicing because:**

1. **Different scope:**
   - GPU time-slicing = cluster-wide GPU operator config
   - JupyterHub = namespace-scoped application

2. **Different components:**
   - GPU time-slicing = NVIDIA GPU Operator (ClusterPolicy)
   - JupyterHub = Hub, Proxy, user pods

3. **Separation of concerns:**
   - Infrastructure config (GPU) ≠ Application config (JupyterHub)

**This is why you need a separate setup step!**

### Shell Script vs Pure YAML

**Shell Script:**
- Imperative ("do these steps")
- Good for automation
- Hard to version control
- Includes logic & verification

**Pure K8s YAML:**
- Declarative ("I want this state")
- Good for GitOps
- Easy to version control
- No logic, just desired state

Both achieve the same result!

---

## ✅ All 4 Options Are Now Available

Choose the one that fits your workflow:

1. **`helm/setup-gpu-timeslicing.sh`** - Shell script (Helm dir)
2. **`k8s-manifests/setup-gpu-timeslicing.sh`** - Shell script (k8s dir)
3. **`helm/gpu-timeslicing-chart/`** - Helm chart
4. **`k8s-manifests/gpu-timeslicing/`** - Pure K8s YAML

**They all do the same thing** - enable 4 users to share your RTX 5090! 🚀

