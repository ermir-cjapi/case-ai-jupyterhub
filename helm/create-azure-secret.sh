#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Create Kubernetes Secret for Azure AD Authentication
# =============================================================================
# Creates a Kubernetes secret containing Azure AD credentials for JupyterHub.
# Run this ONCE before deploying JupyterHub.
#
# Usage:
#   ./create-azure-secret.sh
#
# Or with environment variables:
#   export AZURE_TENANT_ID="your-tenant-id"
#   export AZURE_CLIENT_ID="your-client-id"
#   export AZURE_CLIENT_SECRET="your-client-secret"
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

# Validate inputs
if [ -z "${AZURE_TENANT_ID}" ] || [ -z "${AZURE_CLIENT_ID}" ] || [ -z "${AZURE_CLIENT_SECRET}" ]; then
    echo "❌ Error: All three values are required!"
    exit 1
fi

# Check if secret exists and ask to replace
if kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" >/dev/null 2>&1; then
    echo ""
    echo "⚠️  Secret '${SECRET_NAME}' already exists."
    read -p "Replace it? (y/N): " REPLACE
    if [[ ! "${REPLACE}" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    kubectl delete secret "${SECRET_NAME}" -n "${NAMESPACE}"
fi

# Create namespace if needed
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Create the secret
echo ""
echo "Creating secret..."
kubectl create secret generic "${SECRET_NAME}" \
    --namespace "${NAMESPACE}" \
    --from-literal=tenant-id="${AZURE_TENANT_ID}" \
    --from-literal=client-id="${AZURE_CLIENT_ID}" \
    --from-literal=client-secret="${AZURE_CLIENT_SECRET}"

echo ""
echo "✅ Secret created successfully!"
echo ""
echo "Next step:"
echo "  ./deploy_jhub_helm.sh"
echo ""
