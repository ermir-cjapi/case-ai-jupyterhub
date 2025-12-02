# JupyterHub Configuration for Docker Compose Testing
# Azure AD / Entra ID Authentication

import os

# Use DockerSpawner to create containers for each user
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Network setup
c.DockerSpawner.network_name = 'jupyterhub-network'
c.DockerSpawner.remove = True  # Remove containers when users logout
c.DockerSpawner.use_internal_ip = True

# Hub connection settings
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.hub_connect_ip = 'jupyterhub'

# Timeouts
c.Spawner.start_timeout = 300
c.Spawner.http_timeout = 120

# Notebook image
c.DockerSpawner.image = 'jupyter/scipy-notebook:latest'

# Mount a volume for persistent notebooks
c.DockerSpawner.notebook_dir = '/home/jovyan/work'
c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/jovyan/work'
}

# Resource limits
c.DockerSpawner.cpu_limit = 2.0
c.DockerSpawner.mem_limit = '4G'

# ============================================
# AZURE AD / ENTRA ID AUTHENTICATION
# ============================================
# Instructions:
# 1. Go to Azure Portal → Microsoft Entra ID → App registrations
# 2. Click "New registration"
# 3. Fill in:
#    - Name: JupyterHub Local Test
#    - Supported account types: Single tenant (or Multi-tenant)
#    - Redirect URI: Web → http://localhost:8000/hub/oauth_callback
# 4. After creation:
#    - Copy "Application (client) ID" → CLIENT_ID below
#    - Copy "Directory (tenant) ID" → TENANT_ID below
# 5. Go to "Certificates & secrets" → New client secret
#    - Copy the secret value → CLIENT_SECRET below
# 6. Go to "API permissions":
#    - Add permission → Microsoft Graph → Delegated
#    - Add: email, openid, profile, User.Read
#    - (Optional for groups): GroupMember.Read.All
# 7. Restart: docker-compose restart
# ============================================

from oauthenticator.azuread import AzureAdOAuthenticator

c.JupyterHub.authenticator_class = AzureAdOAuthenticator

# PASTE YOUR AZURE AD / ENTRA ID CREDENTIALS HERE:
c.AzureAdOAuthenticator.tenant_id = 'YOUR_TENANT_ID_HERE'
c.AzureAdOAuthenticator.client_id = 'YOUR_CLIENT_ID_HERE'
c.AzureAdOAuthenticator.client_secret = 'YOUR_CLIENT_SECRET_HERE'
c.AzureAdOAuthenticator.oauth_callback_url = 'http://localhost:8000/hub/oauth_callback'

# Allow all users from your Azure AD tenant
c.Authenticator.allow_all = True

# ============================================
# ROLES AND ACCESS CONTROL
# ============================================

# Option 1: Allow specific users (by email or username)
# c.Authenticator.allowed_users = {'user1@yourdomain.com', 'user2@yourdomain.com'}

# Option 2: Allow specific Azure AD groups (requires GroupMember.Read.All permission)
# c.AzureAdOAuthenticator.allowed_groups = {'JupyterHub-Users', 'Data-Scientists'}

# Option 3: Admin users (by email)
c.Authenticator.admin_users = {'your-email@yourdomain.com'}

# Option 4: Admin groups (Azure AD group names)
# c.AzureAdOAuthenticator.admin_groups = {'JupyterHub-Admins'}

# ============================================
# GITHUB AUTHENTICATION (COMMENTED OUT)
# ============================================
# from oauthenticator.github import GitHubOAuthenticator
# c.JupyterHub.authenticator_class = GitHubOAuthenticator
# c.GitHubOAuthenticator.client_id = 'Ov23liKKs5nB8rIidz6c'
# c.GitHubOAuthenticator.client_secret = '4e00e0e9180367632a029e384a4599b1f4886413'
# c.GitHubOAuthenticator.oauth_callback_url = 'http://localhost:8000/hub/oauth_callback'
# c.Authenticator.allow_all = True
# c.Authenticator.admin_users = {'your-github-username'}

# ============================================
# SIMPLE AUTH (NO OAUTH - FOR TESTING)
# ============================================
# c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'
# c.DummyAuthenticator.password = ""
# c.Authenticator.admin_users = {'admin'}

# Delete idle notebooks after 1 hour
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': [
            'python3', '-m', 'jupyterhub_idle_culler',
            '--timeout=3600'
        ],
    }
]
