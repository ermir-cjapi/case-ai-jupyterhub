# GPU User Profiles Guide

## Overview

Your JupyterHub now has **two profile options** that users select when logging in:

```
┌─────────────────────────────────────────────────────┐
│          JupyterHub Login Screen                    │
│                                                     │
│  Choose your server profile:                       │
│                                                     │
│  ○ 💻 CPU Only - Data Exploration                  │
│     Always available (no waiting)                  │
│     2 CPUs, 4GB RAM                                │
│                                                     │
│  ○ 🎮 GPU Enabled - ML/AI Training                 │
│     1 GPU slice (RTX 5090)                         │
│     4 CPUs, 8GB RAM, 1 GPU                         │
│     May queue if 8 users active                    │
│                                                     │
│           [Start My Server]                        │
└─────────────────────────────────────────────────────┘
```

---

## Profile Details

### Profile 1: CPU Only - Data Exploration

**Resources:**
- ✅ 2 CPUs (0.5 guaranteed)
- ✅ 4GB RAM (1GB guaranteed)
- ❌ No GPU

**Best for:**
- Data exploration and analysis
- Pandas/NumPy operations
- Data visualization (Matplotlib, Plotly)
- Reading documentation
- Writing code without training models

**Availability:**
- 🚀 **Always starts immediately**
- ♾️ **Unlimited concurrent users**

**When to use:**
- "I'm just exploring data"
- "I'm doing statistics/visualization"
- "I don't need GPU right now"

---

### Profile 2: GPU Enabled - ML/AI Training

**Resources:**
- ✅ 4 CPUs (1 guaranteed)
- ✅ 8GB RAM (2GB guaranteed)
- ✅ **1 GPU slice** (1/8 of RTX 5090 with time-slicing)

**Best for:**
- Training PyTorch/TensorFlow models
- Running transformers/LLMs
- Computer vision (OpenCV, object detection)
- Any GPU-accelerated workload

**Availability:**
- 🎮 **Up to 8 users simultaneously**
- ⏳ **User #9 waits in queue** until someone logs out

**When to use:**
- "I'm training a neural network"
- "I need to run inference on a large model"
- "I'm using GPU-accelerated libraries"

---

## How GPU Sharing Works

### With 8-Replica Time-Slicing:

```
RTX 5090 (32GB VRAM)
│
├─ GPU Slice 1 → User Alice  (training ResNet)
├─ GPU Slice 2 → User Bob    (running BERT)
├─ GPU Slice 3 → User Carol  (doing inference)
├─ GPU Slice 4 → User Dave   (testing code)
├─ GPU Slice 5 → User Emma   (training GAN)
├─ GPU Slice 6 → User Frank  (processing images)
├─ GPU Slice 7 → User Grace  (running analysis)
└─ GPU Slice 8 → User Henry  (training model)

User Iris → ⏳ Pending (waiting for a slot)
```

**Performance distribution:**
- If 1 user active: Gets 100% of GPU
- If 2 users active: Each gets ~50% of GPU
- If 8 users active: Each gets ~12.5% of GPU

---

## User Experience Examples

### Scenario 1: Data Scientist (CPU-only work)

```python
# Alice selects "CPU Only" profile
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('sales_data.csv')
df.groupby('region').sum().plot(kind='bar')
plt.show()

# ✅ Starts immediately
# ✅ Fast for data operations
# ✅ No wasted GPU resources
```

---

### Scenario 2: ML Engineer (GPU training)

```python
# Bob selects "GPU Enabled" profile
import torch
import torch.nn as nn

device = torch.device("cuda")  # GPU available
model = nn.Sequential(...).to(device)

# Train model
for epoch in range(100):
    train(model, data, device)

# ✅ Gets GPU access
# ✅ Can train models efficiently
# ⏳ May wait if 8 other users are active
```

---

### Scenario 3: Smart User (switches profiles)

**Morning (data exploration):**
- Selects "CPU Only"
- Loads data, cleans it, visualizes
- Starts immediately

**Afternoon (model training):**
- Logs out, selects "GPU Enabled"
- Trains neural network with GPU
- May wait briefly if GPU busy

**Benefits:**
- Not blocking GPU when not needed
- Others can use GPU during exploration phase

---

## Admin Monitoring

### Check who's using GPUs:

```bash
# See all running user pods
kubectl get pods -n jupyterhub-test -l component=singleuser-server

# Check GPU allocation
kubectl describe nodes | grep -A5 "Allocated resources:" | grep nvidia

# Monitor GPU usage in real-time
watch -n 1 nvidia-smi
```

### Example output:

```
NAME                    READY   STATUS    GPU
jupyter-alice-xxx       1/1     Running   1/1 GPU  ← GPU profile
jupyter-bob-xxx         1/1     Running   1/1 GPU  ← GPU profile
jupyter-carol-xxx       1/1     Running   0/1 GPU  ← CPU profile
jupyter-dave-xxx        1/1     Running   1/1 GPU  ← GPU profile
```

---

## Configuration

### Change GPU user limit (e.g., 16 users instead of 8):

```bash
# Edit setup-gpu-timeslicing.sh
REPLICAS=16  # Change from 8 to 16

# Rerun script
./setup-gpu-timeslicing.sh

# Redeploy JupyterHub
cd helm && ./deploy_jhub_helm.sh
```

### Adjust CPU-only resources:

Edit `helm/values-helm.yaml`:

```yaml
profileList:
  - display_name: "💻 CPU Only"
    kubespawner_override:
      cpu_limit: 4        # Increase to 4 CPUs
      mem_limit: "8G"     # Increase to 8GB RAM
```

---

## Best Practices

### For Users:

1. **Choose CPU profile by default** unless you explicitly need GPU
2. **Log out when done** to free up GPU slots for others
3. **Save your work frequently** (idle servers shut down after 1 hour)
4. **Monitor your GPU usage** with `nvidia-smi` in terminal

### For Admins:

1. **Monitor GPU utilization** to see if 8 slots is enough
2. **Adjust REPLICAS** if users frequently queue
3. **Set appropriate idle timeout** (currently 1 hour)
4. **Educate users** about profile selection

---

## Troubleshooting

### "My GPU profile is stuck on 'Pending'"

**Cause:** All 8 GPU slots occupied.

**Solutions:**
1. Wait for another user to log out (check back in 10-15 min)
2. Use CPU profile if you don't need GPU immediately
3. Contact admin to increase GPU replicas

---

### "I selected GPU but torch.cuda.is_available() returns False"

**Check:**
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"PyTorch version: {torch.__version__}")

# If False, you might have selected CPU profile by mistake
# Log out and select "GPU Enabled" profile
```

---

### "I can't see profile selection screen"

**Cause:** You might have a running server already.

**Solution:**
1. Go to `File > Hub Control Panel`
2. Click "Stop My Server"
3. Click "Start My Server" → profile selection appears

---

## Summary

| Feature | CPU Profile | GPU Profile |
|---------|-------------|-------------|
| **Resources** | 2 CPU, 4GB RAM | 4 CPU, 8GB RAM, 1 GPU |
| **Max Users** | Unlimited | 8 concurrent |
| **Start Time** | Immediate | May queue |
| **Best For** | Data analysis | Model training |
| **Cost** | Low compute | High compute |

**Remember:** Choose the right tool for the job! 🎯

