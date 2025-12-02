# JupyterHub Configuration with GPU Support
# Spawns GPU-enabled notebook containers

import os

# Use DockerSpawner
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Network setup
c.DockerSpawner.network_name = 'jupyterhub-network'
c.DockerSpawner.remove = True
c.DockerSpawner.use_internal_ip = True

# GPU-enabled notebook image
# You can use your custom image: docker.io/ermircjapi/jupyterhub-notebook:latest
c.DockerSpawner.image = 'jupyter/tensorflow-notebook:latest'  # Has GPU support

# Mount volume for persistent notebooks
c.DockerSpawner.notebook_dir = '/home/jovyan/work'
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/jovyan/work'
}

# Resource limits with GPU
c.DockerSpawner.cpu_limit = 4.0
c.DockerSpawner.mem_limit = '16G'

# GPU configuration - give each user 1 GPU
c.DockerSpawner.extra_host_config = {
    'device_requests': [
        {
            'Driver': 'nvidia',
            'Count': 1,  # Number of GPUs per user
            'Capabilities': [['gpu', 'compute', 'utility']]
        }
    ]
}

# Simple authentication
c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
c.DummyAuthenticator.password = ""
c.Authenticator.admin_users = {'admin'}

# Hub configuration
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'

# Auto-shutdown idle notebooks
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': [
            'python3', '-m', 'jupyterhub_idle_culler',
            '--timeout=3600'
        ],
    }
]

