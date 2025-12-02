# Local JupyterHub Testing with Docker Compose

Test JupyterHub locally before deploying to Kubernetes.

## What is JupyterHub?

**JupyterHub** = Multi-user Jupyter Notebook server

- **Single User Jupyter**: You run `jupyter notebook` on your laptop → one person only
- **JupyterHub**: Multiple users login to one server → each gets their own isolated notebook environment

### How It Works

```
User1 logs in → JupyterHub spawns container → User1 gets Jupyter notebook
User2 logs in → JupyterHub spawns container → User2 gets Jupyter notebook
User3 logs in → JupyterHub spawns container → User3 gets Jupyter notebook
```

Each container is isolated:
- Separate file storage
- Separate processes
- Can have different resources (CPU, RAM, GPU)

## Quick Test (CPU-only)

### 1. Install Docker Compose

Already installed with Docker Desktop.

### 2. Start JupyterHub

```bash
# CPU-only version (for testing)
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access

Open browser: **http://localhost:8000**

- Username: anything (e.g., `user1`, `admin`)
- Password: just press Enter (no password)

### 4. Test

Click "Start My Server" → You get your own Jupyter notebook!

Open another browser (incognito) → Login as `user2` → Separate notebook!

### 5. Stop

```bash
docker-compose down
```

## GPU Testing

### Prerequisites

- NVIDIA GPU
- NVIDIA Docker runtime installed

### Start with GPU

```bash
# GPU-enabled version
docker-compose -f docker-compose-gpu.yml up -d

# Check logs
docker-compose -f docker-compose-gpu.yml logs -f
```

### Test GPU in Notebook

After logging in, create a new notebook:

```python
# Test 1: Check GPU availability
import tensorflow as tf
print("GPUs Available:", tf.config.list_physical_devices('GPU'))

# Test 2: PyTorch GPU
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

# Test 3: Run computation on GPU
x = torch.rand(1000, 1000).cuda()
y = torch.rand(1000, 1000).cuda()
z = torch.matmul(x, y)
print(f"Computation device: {z.device}")  # Should show "cuda:0"
```

### Stop GPU Version

```bash
docker-compose -f docker-compose-gpu.yml down
```

## Understanding GPU Configuration

### Current Kubernetes Config

In `infra/jupyterhub/values-v1.yaml`, GPU is **commented out** (disabled):

```yaml
# GPU profile (uncomment to enable GPU support)
# extraResource:
#   limits:
#     nvidia.com/gpu: "1"
```

To enable GPU in Kubernetes deployment, **uncomment** those lines:

```yaml
singleuser:
  extraResource:
    limits:
      nvidia.com/gpu: "1"    # Each user gets 1 GPU
    guarantees:
      nvidia.com/gpu: "1"
```

### What Happens When GPU is Enabled?

**With GPU enabled:**
- Each user's notebook container gets access to 1 GPU
- Python code runs on GPU: `torch.cuda.is_available()` → `True`
- ML models train on GPU: `model.cuda()` → uses GPU
- Faster training for deep learning models

**Without GPU (default):**
- Notebooks run on CPU only
- Python code works but slower for ML
- Good for data analysis, visualization, non-ML tasks

### Example: Who Gets GPU?

```yaml
# Option 1: Everyone gets GPU (current config if uncommented)
singleuser:
  extraResource:
    limits:
      nvidia.com/gpu: "1"

# Option 2: User chooses (multiple profiles)
singleuser:
  profileList:
    - display_name: "CPU Only (2GB RAM)"
      kubespawner_override:
        cpu_limit: 2
        mem_limit: 2G
    
    - display_name: "GPU (16GB RAM + 1 GPU)"
      kubespawner_override:
        cpu_limit: 4
        mem_limit: 16G
        extra_resource_limits:
          nvidia.com/gpu: "1"
```

With profiles, users choose at spawn time:
- "I need GPU for training" → selects GPU profile
- "Just analyzing CSV files" → selects CPU profile

## What Can You Do in JupyterHub Notebooks?

### Data Science

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Analyze
df.describe()

# Visualize
df.plot()
plt.show()
```

### Machine Learning (CPU)

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris

# Load data
X, y = load_iris(return_X_y=True)

# Train model
model = RandomForestClassifier()
model.fit(X, y)

# Predict
predictions = model.predict(X)
```

### Deep Learning (GPU)

```python
import torch
import torch.nn as nn

# Move to GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Define model
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
).to(device)

# Training runs on GPU!
# Data and model both on GPU = fast training
```

### Computer Vision

```python
from transformers import pipeline

# Image classification (uses GPU if available)
classifier = pipeline("image-classification")
result = classifier("cat.jpg")
print(result)
```

## Docker Compose vs Kubernetes

### Docker Compose (Local Testing)
- ✅ Simple, quick setup
- ✅ Good for testing JupyterHub features
- ✅ Test GPU allocation
- ❌ Single server only
- ❌ No high availability
- ❌ Manual management

### Kubernetes (Production - Current Setup)
- ✅ Production-grade
- ✅ Scales across multiple servers
- ✅ Automatic restarts if crashes
- ✅ Resource management
- ✅ Persistent storage
- ✅ Monitoring & logging
- ✅ Cloudflare integration

## Recommendation

1. **Test locally first** with Docker Compose
   - Understand how JupyterHub works
   - Test GPU allocation
   - See the multi-user experience

2. **Then deploy to Kubernetes** (your NVIDIA server)
   - Production setup
   - Accessible via Cloudflare
   - Persistent storage
   - Better resource management

## Next Steps

### Local Testing
```bash
# Test CPU version
docker-compose up -d
open http://localhost:8000

# Test GPU version
docker-compose -f docker-compose-gpu.yml up -d
# Create notebook and test torch.cuda.is_available()
```

### Then Deploy to Kubernetes
```bash
# Once satisfied with local testing
source lab-config.env
./scripts/build_base_image.sh
./scripts/deploy_jhub_v1.sh
# Access at https://jupyterhub.ccrolabs.com
```

---

**Summary:**
- JupyterHub = multi-user Jupyter server
- Docker Compose = quick local testing
- Kubernetes = production deployment
- GPU = enabled per notebook for ML/DL workloads

