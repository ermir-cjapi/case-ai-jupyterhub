# What is jupyterhub_config.py?

The `jupyterhub_config.py` file is the **configuration file** for JupyterHub. It tells JupyterHub how to behave.

## Think of it Like This

JupyterHub is like a **restaurant manager**:
- **jupyterhub_config.py** = The manager's rulebook
- It defines: Who can enter? What do they get? How much can they have?

## What Does It Configure?

### 1. **How to Create User Notebooks** (Spawner)

```python
# Use Docker to create notebook containers
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
```

**Translation:** "When a user logs in, create a Docker container for their notebook"

### 2. **Which Notebook Image to Use**

```python
# Which Docker image has Jupyter + Python + Libraries?
c.DockerSpawner.image = 'jupyter/scipy-notebook:latest'
```

**Translation:** "Each user gets a container based on this image (has Python, pandas, numpy, etc.)"

### 3. **Resource Limits**

```python
# CPU and RAM per user
c.DockerSpawner.cpu_limit = 2.0      # Max 2 CPUs
c.DockerSpawner.mem_limit = '4G'     # Max 4GB RAM
```

**Translation:** "Each user can use at most 2 CPU cores and 4GB of memory"

### 4. **Authentication** (Who Can Login)

```python
# Simple auth - anyone can login with any username
c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.DummyAuthenticator.password = ""  # No password
```

**Translation:** "Anyone can login with any username, no password required" (good for testing!)

**Other options:**
```python
# GitHub OAuth - login with GitHub account
c.JupyterHub.authenticator_class = 'oauthenticator.github.GitHubOAuthenticator'

# LDAP - login with company credentials
c.JupyterHub.authenticator_class = 'ldapauthenticator.LDAPAuthenticator'

# Custom password - everyone uses same password
c.DummyAuthenticator.password = "secret123"
```

### 5. **Admin Users**

```python
# Who gets admin privileges?
c.Authenticator.admin_users = {'admin', 'alice'}
```

**Translation:** "Users 'admin' and 'alice' can manage other users, stop their servers, etc."

### 6. **Storage/Persistence**

```python
# Where to save user notebooks?
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/jovyan/work'
}
```

**Translation:** "Create a persistent volume for each user's files. When they logout and login again, their notebooks are still there!"

### 7. **GPU Configuration** (in jupyterhub_config_gpu.py)

```python
# Give each user 1 GPU
c.DockerSpawner.extra_host_config = {
    'device_requests': [
        {
            'Driver': 'nvidia',
            'Count': 1,  # 1 GPU per user
            'Capabilities': [['gpu', 'compute', 'utility']]
        }
    ]
}
```

**Translation:** "Each user's notebook container gets access to 1 NVIDIA GPU"

### 8. **Auto-Shutdown Idle Notebooks**

```python
# Shutdown notebooks after 1 hour of inactivity
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': ['python3', '-m', 'jupyterhub_idle_culler', '--timeout=3600']
    }
]
```

**Translation:** "If a user doesn't use their notebook for 1 hour, automatically shut it down to save resources"

## Real World Example

Let's say you have this config:

```python
# jupyterhub_config.py

# Use Docker to spawn notebooks
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Each user gets this image (Python + ML libraries)
c.DockerSpawner.image = 'jupyter/tensorflow-notebook:latest'

# Resource limits
c.DockerSpawner.cpu_limit = 4.0
c.DockerSpawner.mem_limit = '8G'

# Give 1 GPU to each user
c.DockerSpawner.extra_host_config = {
    'device_requests': [{'Driver': 'nvidia', 'Count': 1, 'Capabilities': [['gpu']]}]
}

# Anyone can login, no password
c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.DummyAuthenticator.password = ""

# Alice is admin
c.Authenticator.admin_users = {'alice'}

# Persistent storage per user
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/jovyan/work'
}
```

**What happens when Bob logs in?**

1. JupyterHub creates a Docker container from `tensorflow-notebook` image
2. Gives it 4 CPUs, 8GB RAM, 1 GPU
3. Mounts a volume named `jupyterhub-user-bob` to `/home/jovyan/work`
4. Bob gets Jupyter notebook in browser
5. Bob's Python code can use GPU: `torch.cuda.is_available()` → `True`
6. Bob saves `my_model.py` → Stored in his persistent volume
7. Bob logs out → Container is deleted
8. Bob logs in again tomorrow → New container, but volume is mounted again, `my_model.py` is still there!

## Two Configs in This Repo

### `jupyterhub_config.py` (CPU-only)
- No GPU
- Uses `jupyter/scipy-notebook` image (lighter)
- 2 CPUs, 4GB RAM per user
- Good for: Testing, data analysis, non-ML work

### `jupyterhub_config_gpu.py` (GPU-enabled)
- 1 GPU per user
- Uses `jupyter/tensorflow-notebook` image (has GPU support)
- 4 CPUs, 16GB RAM per user
- Good for: Deep learning, training models

## How to Modify Config

Want to change something? Edit the config file!

### Example: Change resource limits

```python
# Give each user more resources
c.DockerSpawner.cpu_limit = 8.0      # 8 CPUs instead of 2
c.DockerSpawner.mem_limit = '32G'    # 32GB instead of 4GB
```

### Example: Add password

```python
# Require password
c.DummyAuthenticator.password = "my-secret-password"
```

### Example: Use your custom image

```python
# Use your own notebook image from Docker Hub
c.DockerSpawner.image = 'ermircjapi/my-custom-notebook:latest'
```

### Example: Give 2 GPUs per user

```python
c.DockerSpawner.extra_host_config = {
    'device_requests': [
        {
            'Driver': 'nvidia',
            'Count': 2,  # 2 GPUs instead of 1
            'Capabilities': [['gpu', 'compute', 'utility']]
        }
    ]
}
```

## Config vs Kubernetes values.yaml

**Docker Compose** (local testing):
- Uses `jupyterhub_config.py`
- Python-based configuration
- Simple, all in one file

**Kubernetes** (production deployment):
- Uses `infra/jupyterhub/values-v1.yaml`
- YAML-based configuration
- More complex but more powerful

**They do the same thing**, just different formats!

## Summary

**jupyterhub_config.py** tells JupyterHub:
1. ✅ How to create user notebooks (Docker containers)
2. ✅ What image to use (which Python libraries available)
3. ✅ Resource limits (CPU, RAM, GPU)
4. ✅ Who can login (authentication)
5. ✅ Who is admin
6. ✅ Where to store files (persistence)
7. ✅ Auto-shutdown rules

**Without it:** JupyterHub doesn't know what to do!

**With it:** JupyterHub knows exactly how to manage users and their notebooks.

