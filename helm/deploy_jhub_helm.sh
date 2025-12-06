#!/usr/bin/env bash
set -euo pipefail

# Configuration from lab-config.env or defaults
NAMESPACE="${NAMESPACE:-jupyterhub-test}"
RELEASE_NAME="${RELEASE_NAME:-jhub-v1}"
VALUES_FILE="${VALUES_FILE:-helm/values-helm.yaml}"
CHART_VERSION="${CHART_VERSION:-3.3.8}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "=== JupyterHub Deployment ==="
echo "Namespace: ${NAMESPACE}"
echo "Release: ${RELEASE_NAME}"
echo "Values: ${VALUES_FILE}"
echo "Chart Version: ${CHART_VERSION}"
echo ""

# Add JupyterHub Helm repo
echo "Adding JupyterHub Helm repo..."
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart >/dev/null 2>&1 || true
helm repo update jupyterhub

# Deploy JupyterHub
# Helm will automatically:
# - Create namespace if it doesn't exist (with --create-namespace)
# - Create all required resources (services, deployments, PVCs, etc.)
# - Configure everything from values-v1.yaml
echo "Deploying JupyterHub ${RELEASE_NAME} to namespace ${NAMESPACE}..."
helm upgrade --install "${RELEASE_NAME}" jupyterhub/jupyterhub \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --version "${CHART_VERSION}" \
  --values "${VALUES_FILE}" \
  --timeout 10m \
  --wait

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Check status:"
echo "  kubectl get pods -n ${NAMESPACE}"
echo ""
echo "View logs:"
echo "  kubectl logs -n ${NAMESPACE} -l component=hub --tail=50"
echo ""
echo "Access JupyterHub:"
echo "  https://jupyterhub.ccrolabs.com"
echo ""
