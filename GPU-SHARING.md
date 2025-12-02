# GPU Sharing for Multiple JupyterHub Users

Enable multiple users to share your RTX 5090 simultaneously using NVIDIA GPU time-slicing.

## 🎯 Problem & Solution

### Without Time-Slicing (Current Default)
- ❌ 1 physical GPU → Only **1 user** at a time
- ❌ User 2, 3, 4... **wait indefinitely** (Pending pods)
- ❌ GPU underutilized if user isn't running intensive tasks

### With Time-Slicing (After Setup)
- ✅ 1 physical GPU → **4 users simultaneously**
- ✅ Fair automatic sharing
- ✅ Each gets ~25% when all active, 100% when alone
- ✅ Better resource utilization

## 🚀 Quick Setup (5 Minutes)

### Run the Setup Script

```bash
cd helm
./setup-gpu-timeslicing.sh
```

This will:
1. Create time-slicing ConfigMap (4 replicas)
2. Configure NVIDIA GPU Operator
3. Restart device plugin
4. Verify setup worked

### Expected Output

```
✅ SUCCESS! Time-slicing is active!

🎉 Configuration Summary:
   Physical GPUs: 1
   Time-slicing replicas: 4
   Virtual GPUs: 4
   Max concurrent JupyterHub users: 4
```

### Verify It Worked

```bash
# Check GPU capacity (should show 4, not 1)
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'

# Should output: "4"
```

## 📊 Performance Expectations

### RTX 5090 with 4 Replicas

| Active Users | Performance per User | Your RTX 5090 |
|--------------|---------------------|---------------|
| 1 user | 100% (full GPU) | 100% available |
| 2 users | ~50% each | 100% utilized |
| 3 users | ~33% each | 100% utilized |
| 4 users | ~25% each | 100% utilized |
| 5+ users | 4 work, rest **wait** | Capped at 4 users |

**Note:** Performance is dynamic - if some users are idle, active users get more resources.

## ⚙️ Configuration Options

### Adjust Number of Users per GPU

Edit `setup-gpu-timeslicing.sh` line 19:

```bash
REPLICAS=4  # Change this value

# Common options:
# 2  = 2 users  (50% each)
# 4  = 4 users  (25% each) ⭐ Recommended for RTX 5090
# 8  = 8 users  (12.5% each)
# 10 = 10 users (10% each)
```

Then run the script again:
```bash
./setup-gpu-timeslicing.sh
```

### RTX 5090 Recommendations (32GB VRAM)

| Replicas | Users | GPU per User | VRAM per User* | Best For |
|----------|-------|--------------|----------------|----------|
| 2 | 2 | 50% | ~16GB | Heavy ML training |
| **4** | **4** | **25%** | **~8GB** | **Mixed workloads** ⭐ |
| 8 | 8 | 12.5% | ~4GB | Light/interactive |

\* Assuming equal usage. VRAM is shared, not hard-partitioned.

## 🔧 JupyterHub Configuration

Your `values-helm.yaml` is **already configured correctly!**

```yaml
singleuser:
  extraResource:
    limits:
      nvidia.com/gpu: "1"  # Each user gets 1 GPU slice
    guarantees:
      nvidia.com/gpu: "1"
```

With time-slicing (4 replicas):
- Each user requests "1" GPU slice
- Kubernetes sees 4 available (time-sliced from 1 physical)
- 4 users can run simultaneously

## 🧪 Testing Multi-User Access

### Step 1: Deploy JupyterHub

```bash
cd helm
./deploy_jhub_helm.sh
```

### Step 2: Have Multiple Users Log In

Open 4 browser windows (or have 4 different users):
- https://jupyterhub.ccrolabs.com

All should be able to log in and start notebooks simultaneously!

### Step 3: Test GPU Access in Notebooks

Each user runs:

```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Simple GPU computation
x = torch.rand(5000, 5000).cuda()
y = torch.rand(5000, 5000).cuda()
z = torch.matmul(x, y)

print("✅ GPU computation successful!")
```

All users should see the RTX 5090 and be able to use it!

## 🔍 Monitoring

### Check Active Users

```bash
# See all running user notebooks
kubectl get pods -n jupyterhub-test | grep jupyter-

# Example output (4 users active):
# jupyter-alice-...    Running
# jupyter-bob-...      Running
# jupyter-charlie-...  Running
# jupyter-diana-...    Running
```

### Monitor GPU Usage

```bash
# Real-time GPU monitoring (on NVIDIA server)
watch -n 1 nvidia-smi

# You'll see multiple processes:
#   PID      Process     GPU Memory
#   12345    python      2500MiB    (alice)
#   12346    python      3200MiB    (bob)
#   12347    python      1800MiB    (charlie)
#   12348    python      2100MiB    (diana)
```

### Check GPU Metrics in Kubernetes

```bash
# GPU utilization per pod
kubectl exec -n gpu-operator -it $(kubectl get pod -n gpu-operator -l app=nvidia-dcgm-exporter -o jsonpath='{.items[0].metadata.name}') -- dcgmi dmon -e 155,156,157
```

## ⚠️ Important Considerations

### 1. GPU Memory is Shared (Not Divided!)

**Critical:** Your RTX 5090 has 32GB VRAM total.

- All users share the same 32GB pool
- If 4 users each try to use 10GB → **Out of Memory Error!**
- Users should limit themselves to ~8GB each (32GB ÷ 4)

**Solution A:** Educate users

```python
# Users should add to their notebooks:
import torch
torch.cuda.set_per_process_memory_fraction(0.25)  # Limit to 25% of 32GB = 8GB
```

**Solution B:** Set global limit in JupyterHub

Add to `values-helm.yaml`:

```yaml
hub:
  extraConfig:
    gpu-memory-limit: |
      c.KubeSpawner.environment = {
          'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:2048',
      }
```

### 2. Performance Varies by Workload

**Works Great:**
- ✅ Interactive data exploration
- ✅ Model inference
- ✅ Training small models
- ✅ Visualization
- ✅ Mixed CPU/GPU workloads

**May Struggle:**
- ⚠️ Heavy 24/7 training
- ⚠️ Large batch processing
- ⚠️ Multiple users with GPU-intensive tasks simultaneously

### 3. Auto-Shutdown Helps

Already configured in `values-helm.yaml`:

```yaml
cull:
  enabled: true
  timeout: 3600  # Auto-shutdown after 1 hour idle
```

This frees up GPU slices from idle users.

## 🛠️ Troubleshooting

### Time-Slicing Not Working (Still Shows 1 GPU)

**Check ConfigMap:**
```bash
kubectl get configmap time-slicing-config -n gpu-operator -o yaml
```

**Check ClusterPolicy:**
```bash
kubectl get clusterpolicy cluster-policy -n gpu-operator -o yaml | grep -A 5 devicePlugin
```

**Restart Device Plugin:**
```bash
kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset
sleep 30
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

### Users Getting "Insufficient nvidia.com/gpu" Error

Time-slicing not enabled yet. Run setup script:
```bash
./setup-gpu-timeslicing.sh
```

### Out of Memory Errors

Users exceeding GPU memory limits.

**Option 1:** Reduce replicas (4 → 2)
```bash
# Edit setup-gpu-timeslicing.sh
REPLICAS=2

# Re-run
./setup-gpu-timeslicing.sh
```

**Option 2:** Add memory limits to notebooks (see above)

### Users Report Slow Performance

Too many replicas or all users running intensive tasks.

**Check actual usage:**
```bash
nvidia-smi
```

**Solution:** Reduce replicas or ask users to stagger heavy workloads.

## 🔄 Disabling Time-Slicing

To revert to 1 user per GPU:

```bash
# Remove the config
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": ""}}}}'

# Restart device plugin
kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset

# Verify (should show 1 again)
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

## 📚 Additional Resources

- [NVIDIA GPU Operator Docs](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html)
- [GPU Time-Slicing Guide](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/gpu-sharing.html)
- [JupyterHub Resource Management](https://z2jh.jupyter.org/en/stable/administrator/optimization.html)

## ✅ Success Checklist

After setup, verify:

- [ ] Setup script completed successfully
- [ ] `kubectl get nodes` shows `nvidia.com/gpu: 4` (not 1)
- [ ] 4 users can log into JupyterHub simultaneously
- [ ] All users see GPU with `torch.cuda.is_available()` → `True`
- [ ] `nvidia-smi` shows multiple Python processes
- [ ] No pods stuck in `Pending` state with GPU errors

## 🎓 What You've Achieved

✅ **Multi-user GPU access** - 4 users vs 1  
✅ **4x better utilization** - GPU rarely idle  
✅ **Fair resource sharing** - Automatic time-slicing  
✅ **Cost-effective** - Maximize hardware investment  
✅ **Production-ready** - Stable NVIDIA technology  

Your JupyterHub is now optimized for team collaboration! 🚀

