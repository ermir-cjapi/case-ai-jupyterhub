# Quick Start - Local JupyterHub Testing

Test JupyterHub on your computer before deploying to Kubernetes.

## Prerequisites

- Docker Desktop installed
- For GPU testing: NVIDIA GPU + NVIDIA Docker runtime

## 🚀 Quick Test (3 commands)

### CPU Version

```bash
cd local-testing

# Start JupyterHub
docker-compose up -d

# Access
open http://localhost:8000
```

**Login:**
- Username: anything (e.g., `alice`, `bob`, `admin`)
- Password: just press Enter (no password)

**Try this:**
1. Login as `alice` → Click "Start My Server"
2. Open another browser (incognito) → Login as `bob` → Click "Start My Server"
3. Two separate notebook environments! 

**Stop:**
```bash
docker-compose down
```

## 🎮 GPU Version

```bash
cd local-testing

# Start with GPU support
docker-compose -f docker-compose-gpu.yml up -d

# Access
open http://localhost:8000
```

**Test GPU in notebook:**
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")

# Run on GPU
x = torch.rand(1000, 1000).cuda()
y = torch.rand(1000, 1000).cuda()
z = torch.matmul(x, y)
print(f"Device: {z.device}")  # Should show "cuda:0"
```

**Stop:**
```bash
docker-compose -f docker-compose-gpu.yml down
```

## 📝 What You're Testing

When you login:
1. JupyterHub creates a **Docker container** just for you
2. You get Jupyter notebook in that container
3. Your files persist (stored in Docker volume)
4. Other users get their own separate containers

## 🔧 Customize

Edit config files to change behavior:

### `jupyterhub_config.py` (CPU version)
```python
# Change resource limits
c.DockerSpawner.cpu_limit = 4.0      # More CPUs
c.DockerSpawner.mem_limit = '8G'     # More RAM

# Add password
c.DummyAuthenticator.password = "secret123"

# Use different image
c.DockerSpawner.image = 'ermircjapi/my-notebook:latest'
```

### `jupyterhub_config_gpu.py` (GPU version)
```python
# Give 2 GPUs per user
c.DockerSpawner.extra_host_config = {
    'device_requests': [
        {'Driver': 'nvidia', 'Count': 2, 'Capabilities': [['gpu']]}
    ]
}
```

After editing, restart:
```bash
docker-compose down
docker-compose up -d
```

## 📚 Files Explained

- **docker-compose.yml** - Runs JupyterHub container
- **jupyterhub_config.py** - Configures JupyterHub behavior (CPU version)
- **docker-compose-gpu.yml** - GPU-enabled version
- **jupyterhub_config_gpu.py** - GPU configuration
- **Dockerfile.jupyterhub** - Custom JupyterHub image with DockerSpawner

See [WHAT-IS-JUPYTERHUB-CONFIG.md](WHAT-IS-JUPYTERHUB-CONFIG.md) for detailed explanation.

## 🎯 Next Steps

Once you understand how JupyterHub works:

1. Stop local testing: `docker-compose down`
2. Go back to main folder: `cd ..`
3. Deploy to Kubernetes (see main README.md)

## 🐛 Troubleshooting

### JupyterHub won't start

```bash
# Check logs
docker-compose logs -f

# Common issue: Port 8000 already in use
# Change port in docker-compose.yml:
ports:
  - "8001:8000"  # Use 8001 instead
```

### Can't spawn notebook

```bash
# Check Docker socket permission
ls -l /var/run/docker.sock

# Check spawner logs
docker logs jupyterhub-test
```

### GPU not working

```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# If fails, install NVIDIA Container Toolkit
```

---

**Ready?** Run `docker-compose up -d` and visit http://localhost:8000!

