# GPU Multi-User Setup - Quick Summary

## ✅ What's Been Updated

All GPU sharing configurations have been added to **both deployment methods**:

### 📁 Helm Deployment (`helm/`)
- ✅ `values-helm.yaml` - Added GPU time-slicing documentation (lines 95-117)
- ✅ `setup-gpu-timeslicing.sh` - **NEW** automated setup script
- ✅ `GPU-SHARING.md` - **NEW** complete guide with troubleshooting

### 📁 K8s Manifests (`k8s-manifests/`)
- ✅ `01-configmap.yaml` - Added GPU time-slicing documentation (lines 21-38)
- ✅ `setup-gpu-timeslicing.sh` - **NEW** automated setup script (same as helm/)
- ✅ `GPU-SHARING.md` - **NEW** complete guide (same as helm/)
- ✅ `README.md` - Added GPU sharing section

### 📁 Main Documentation
- ✅ `README.md` - Updated both deployment workflows to include GPU setup
- ✅ `STRUCTURE.md` - Added GPU sharing files and updated workflow

## 🎯 The Problem You Had

**Before:**
```
1 RTX 5090 → Only 1 JupyterHub user at a time
User 2, 3, 4... → STUCK WAITING (Pending pods)
```

**After GPU Time-Slicing:**
```
1 RTX 5090 → 4 JupyterHub users simultaneously
Each gets ~25% when all active, 100% when alone
```

## 🚀 How to Enable (Choose One Method)

### Option A: Using Helm

```bash
# 1. Enable GPU sharing
cd helm
./setup-gpu-timeslicing.sh

# Expected output:
# ✅ SUCCESS! Time-slicing is active!
# Virtual GPUs: 4
# Max concurrent JupyterHub users: 4

# 2. Deploy JupyterHub (values-helm.yaml already configured)
./deploy_jhub_helm.sh
```

### Option B: Using K8s Manifests

```bash
# 1. Enable GPU sharing
cd k8s-manifests
./setup-gpu-timeslicing.sh

# Expected output:
# ✅ SUCCESS! Time-slicing is active!
# Virtual GPUs: 4
# Max concurrent JupyterHub users: 4

# 2. Deploy JupyterHub (01-configmap.yaml already configured)
./deploy_k8s_manifests.sh
```

## 📊 What You Get

| Scenario | Before | After |
|----------|--------|-------|
| 1 user active | ✅ Works (100% GPU) | ✅ Works (100% GPU) |
| 2 users active | ❌ 1 works, 1 **WAITS** | ✅ Both work (~50% each) |
| 3 users active | ❌ 1 works, 2 **WAIT** | ✅ All work (~33% each) |
| 4 users active | ❌ 1 works, 3 **WAIT** | ✅ All work (~25% each) |
| 5+ users | ❌ 1 works, rest **WAIT** | ⚠️ 4 work, rest **WAIT** |

## ✅ Verify It's Working

```bash
# 1. Check GPU count (should show 4, not 1)
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
# Output: "4"

# 2. Have 4 users log into JupyterHub
# All should be able to start notebooks simultaneously

# 3. Each user runs in notebook:
import torch
print(f"CUDA available: {torch.cuda.is_available()}")  # Should be True
print(f"GPU: {torch.cuda.get_device_name(0)}")         # RTX 5090

# 4. Monitor on NVIDIA server
nvidia-smi
# Should see 4 Python processes using the GPU
```

## 📚 Documentation Files

| File | Location | What It Contains |
|------|----------|------------------|
| `setup-gpu-timeslicing.sh` | `helm/` and `k8s-manifests/` | Automated setup script |
| `GPU-SHARING.md` | `helm/` and `k8s-manifests/` | Complete guide + troubleshooting |
| `values-helm.yaml` | `helm/` | GPU config with comments (lines 95-117) |
| `01-configmap.yaml` | `k8s-manifests/` | GPU config with comments (lines 21-38) |

## ⚙️ Configuration Options

The setup script defaults to **4 users per GPU** (recommended for RTX 5090).

To change this, edit either setup script:

```bash
# In helm/setup-gpu-timeslicing.sh or k8s-manifests/setup-gpu-timeslicing.sh
REPLICAS=4  # Change to 2, 8, or 10

# Common options:
# 2  = 2 users  (50% each)
# 4  = 4 users  (25% each) ⭐ Recommended
# 8  = 8 users  (12.5% each)
# 10 = 10 users (10% each)
```

Then re-run the script:
```bash
./setup-gpu-timeslicing.sh
```

## ⚠️ Important Notes

### GPU Memory is Shared

Your RTX 5090 has **32GB VRAM total**, shared by all users:
- 4 users → ~8GB per user safe limit
- If users exceed limits → Out of Memory errors

**Solution:** Educate users to limit memory:
```python
import torch
torch.cuda.set_per_process_memory_fraction(0.25)  # Max 25% = 8GB
```

### Auto-Shutdown is Enabled

Already configured in both `values-helm.yaml` and `01-configmap.yaml`:
- Idle timeout: 1 hour
- Frees up GPU slices from inactive users

## 🛠️ Troubleshooting

### Time-slicing not working?

See detailed troubleshooting in:
- `helm/GPU-SHARING.md` or
- `k8s-manifests/GPU-SHARING.md`

Quick check:
```bash
# Verify ConfigMap exists
kubectl get configmap time-slicing-config -n gpu-operator

# Restart device plugin
kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset

# Wait 30 seconds, then check
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

## 🎓 Next Steps

1. ✅ **Run setup script** (`./setup-gpu-timeslicing.sh`)
2. ✅ **Deploy JupyterHub** (helm or k8s manifests)
3. ✅ **Test with multiple users** logging in simultaneously
4. ✅ **Monitor usage** with `nvidia-smi`
5. ✅ **Read full guide** if you need customization

---

**All files are ready!** Just run the setup script in your chosen deployment method (helm or k8s-manifests) and deploy! 🚀

