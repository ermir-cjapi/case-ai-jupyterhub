# GPU Time-Slicing - Pure K8s Manifest Approach

Configure GPU time-slicing using only K8s YAML files (no shell script).

## 🎯 What This Does

Enables multiple JupyterHub users to share each GPU:
- 1 physical GPU → 4 virtual GPUs
- 4 concurrent users instead of 1

## 📁 Files

```
gpu-timeslicing/
├── 00-configmap.yaml           # ConfigMap with time-slicing config
├── 01-patch-clusterpolicy.yaml # Instructions for patching ClusterPolicy
└── README.md                   # This file
```

## 🚀 Setup (Pure kubectl)

### Step 1: Apply ConfigMap

```bash
kubectl apply -f gpu-timeslicing/00-configmap.yaml
```

**Verify:**
```bash
kubectl get configmap time-slicing-config -n gpu-operator
```

### Step 2: Patch ClusterPolicy

**Option A: Using kubectl patch (Recommended)**
```bash
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config", "default": "any"}}}}'
```

**Option B: Using kubectl apply**
```bash
kubectl apply -f - <<EOF
apiVersion: nvidia.com/v1
kind: ClusterPolicy
metadata:
  name: cluster-policy
  namespace: gpu-operator
spec:
  devicePlugin:
    config:
      name: time-slicing-config
      default: any
EOF
```

### Step 3: Wait for Device Plugin Restart

```bash
# Wait for rollout (30-60 seconds)
kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n gpu-operator --timeout=120s
```

### Step 4: Verify Time-Slicing Active

```bash
# Check GPU count (should show "4", not "1")
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'

# Or using kubectl describe
kubectl describe node | grep nvidia.com/gpu
```

**Expected output:**
```
nvidia.com/gpu: 4
```

## ⚙️ Configuration

### Change Number of Users per GPU

Edit `00-configmap.yaml` line 16:

```yaml
replicas: 4  # Change to 2, 8, or 10
```

Common options:
- `2` = 2 users (50% each)
- `4` = 4 users (25% each) ⭐ Recommended
- `8` = 8 users (12.5% each)
- `10` = 10 users (10% each)

Then re-apply:
```bash
kubectl apply -f gpu-timeslicing/00-configmap.yaml
kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset
# Wait 30 seconds for restart
```

## 🔄 Alternative: Use Shell Script

If you prefer automation with verification:

```bash
cd ..
./setup-gpu-timeslicing.sh
```

The script does the same thing but includes:
- ✅ Automatic error checking
- ✅ GPU detection
- ✅ Verification of success
- ✅ Helpful error messages

## 🛠️ Troubleshooting

### ConfigMap Applied but Time-Slicing Not Working

**Check if ClusterPolicy is patched:**
```bash
kubectl get clusterpolicy cluster-policy -n gpu-operator -o yaml | grep -A 3 devicePlugin
```

Should show:
```yaml
devicePlugin:
  config:
    default: any
    name: time-slicing-config
```

**Restart device plugin manually:**
```bash
kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset
sleep 30
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

### Still Shows 1 GPU

**Check ConfigMap:**
```bash
kubectl get configmap time-slicing-config -n gpu-operator -o yaml
```

**Check device plugin logs:**
```bash
kubectl logs -n gpu-operator -l app=nvidia-device-plugin-daemonset --tail=50
```

## 🗑️ Disable Time-Slicing

### Remove Configuration

```bash
# Remove ConfigMap reference from ClusterPolicy
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": ""}}}}'

# Restart device plugin
kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset

# Wait and verify (should show "1" again)
sleep 30
kubectl get nodes -o json | jq '.items[].status.capacity."nvidia.com/gpu"'
```

### Delete ConfigMap (Optional)

```bash
kubectl delete configmap time-slicing-config -n gpu-operator
```

## 📊 Comparison: YAML vs Shell Script

| Aspect | Pure K8s YAML | Shell Script |
|--------|---------------|--------------|
| **Declarative** | ✅ Yes | ❌ Imperative |
| **GitOps-friendly** | ✅ Yes | ⚠️ Harder |
| **Error checking** | ❌ Manual | ✅ Automatic |
| **Verification** | ❌ Manual | ✅ Automatic |
| **Learning value** | ✅ High | ⚠️ Abstracted |
| **Production use** | ✅ Good | ✅ Good |

**Recommendation:**
- **Learning/Understanding:** Use YAML files
- **Quick setup/Production:** Use shell script
- **GitOps/IaC:** Use YAML with ArgoCD/Flux

## ✅ Next Steps

After GPU time-slicing is enabled:

1. Deploy JupyterHub:
   ```bash
   cd ..
   kubectl apply -f .
   ```

2. Test with multiple users logging in

3. Monitor GPU usage:
   ```bash
   nvidia-smi
   ```

---

**Both approaches work!** Choose what fits your workflow:
- **Pure K8s:** More control, better for GitOps
- **Shell script:** Faster, includes verification

