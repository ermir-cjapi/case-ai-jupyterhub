#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Create Kubernetes Secret for Azure AD Authentication
# =============================================================================
# This script creates a Kubernetes secret containing Azure AD credentials.
# Run this ONCE on your NVIDIA server before deploying JupyterHub.
#
# Usage:
#   ./create-azure-secret.sh
#
# The script will prompt you for:
#   - Tenant ID
#   - Client ID  
#   - Client Secret (the VALUE, not the ID!)
#   - (Optional) App Resource / Audience (Application ID or Application ID URI)
#
# Or set environment variables before running:
#   export AZURE_TENANT_ID="your-tenant-id"
#   export AZURE_CLIENT_ID="your-client-id"
#   export AZURE_CLIENT_SECRET="your-client-secret"
#   # Optional but recommended: resource / audience for JupyterHub app
#   # Usually the Application (client) ID or Application ID URI:
#   #   e.g. AZURE_APP_RESOURCE="api://9144a933-3898-411a-b358-e7288a89bcde"
#   export AZURE_APP_RESOURCE="your-app-resource"
#   ./create-azure-secret.sh
# =============================================================================

NAMESPACE="${NAMESPACE:-jupyterhub-test}"
SECRET_NAME="jupyterhub-azure-oauth"

echo "=== Create Azure AD Secret for JupyterHub ==="
echo ""
echo "Namespace: ${NAMESPACE}"
echo "Secret Name: ${SECRET_NAME}"
echo ""

# Get Tenant ID
if [ -z "${AZURE_TENANT_ID:-}" ]; then
    read -p "Enter Azure Tenant ID: " AZURE_TENANT_ID
fi

# Get Client ID
if [ -z "${AZURE_CLIENT_ID:-}" ]; then
    read -p "Enter Azure Client ID: " AZURE_CLIENT_ID
fi

# Get Client Secret (hidden input)
if [ -z "${AZURE_CLIENT_SECRET:-}" ]; then
    read -s -p "Enter Azure Client Secret (VALUE, not ID!): " AZURE_CLIENT_SECRET
    echo ""
fi

# Get App Resource / Audience (optional but recommended)
if [ -z "${AZURE_APP_RESOURCE:-}" ]; then
    read -p "Enter Azure App Resource / Audience (Application ID or Application ID URI, e.g. api://<client-id>) [press Enter to use client-id]: " AZURE_APP_RESOURCE_INPUT
    if [ -n "${AZURE_APP_RESOURCE_INPUT}" ]; then
        AZURE_APP_RESOURCE="${AZURE_APP_RESOURCE_INPUT}"
    else
        AZURE_APP_RESOURCE=""
    fi
fi

# Validate inputs
if [ -z "${AZURE_TENANT_ID}" ] || [ -z "${AZURE_CLIENT_ID}" ] || [ -z "${AZURE_CLIENT_SECRET}" ]; then
    echo "❌ Error: Tenant ID, Client ID and Client Secret are required!"
    exit 1
fi

# Check if secret exists and ask to replace
if kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" >/dev/null 2>&1; then
    echo ""
    echo "⚠️  Secret '${SECRET_NAME}' already exists in namespace '${NAMESPACE}'."
    read -p "Do you want to replace it? (y/N): " REPLACE
    if [[ ! "${REPLACE}" =~ ^[Yy]$ ]]; then
        echo "Cancelled. Existing secret unchanged."
        exit 0
    fi
    echo "Deleting existing secret..."
    kubectl delete secret "${SECRET_NAME}" -n "${NAMESPACE}"
fi

# Create namespace if it doesn't exist
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Create the secret
echo ""
echo "Creating Kubernetes secret..."
kubectl create secret generic "${SECRET_NAME}" \
    --namespace "${NAMESPACE}" \
    --from-literal=tenant-id="${AZURE_TENANT_ID}" \
    --from-literal=client-id="${AZURE_CLIENT_ID}" \
    --from-literal=client-secret="${AZURE_CLIENT_SECRET}" \
    --from-literal=app-resource="${AZURE_APP_RESOURCE}"

echo ""
echo "=== Secret Created Successfully! ==="
echo ""
echo "Secret Details:"
echo "  Name: ${SECRET_NAME}"
echo "  Namespace: ${NAMESPACE}"
echo "  Keys: tenant-id, client-id, client-secret, app-resource"
echo ""
echo "Verify with:"
echo "  kubectl get secret ${SECRET_NAME} -n ${NAMESPACE}"
echo ""
echo "Next step:"
echo "  cd helm && ./deploy_jhub_helm.sh"
echo ""

