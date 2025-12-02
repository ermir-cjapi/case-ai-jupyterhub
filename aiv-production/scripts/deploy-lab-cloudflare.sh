#!/usr/bin/env bash
# Deploy JupyterHub to Lab Environment (Cloudflare Tunnel)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

# Load lab configuration
if [ -f "lab-config.env" ]; then
    source lab-config.env
    echo "✓ Loaded lab-config.env"
else
    echo "Error: lab-config.env not found"
    echo "Create it from lab-config.env.template"
    exit 1
fi

# Override with lab-specific settings
export NAMESPACE="${JHUB_NAMESPACE:-jupyterhub-test}"
export RELEASE_NAME="${RELEASE_NAME:-jhub-lab}"
export VALUES_FILE="infra/jupyterhub/values-lab-cloudflare.yaml"
export CHART_VERSION="${CHART_VERSION:-2.0.0}"

echo "=== JupyterHub Lab Deployment (Cloudflare) ==="
echo ""
echo "Environment: Lab (Cloudflare Tunnel)"
echo "Namespace: ${NAMESPACE}"
echo "Release: ${RELEASE_NAME}"
echo "Domain: ${JHUB_HOST}"
echo "Values: ${VALUES_FILE}"
echo ""

# Check if Cloudflare tunnel is running
if ! systemctl is-active --quiet cloudflared 2>/dev/null; then
    echo "⚠ Warning: Cloudflare tunnel (cloudflared) is not running"
    echo "Run: sudo systemctl start cloudflared"
    echo "Or: ./scripts/setup-cloudflare-tunnel.sh"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Ensure namespace exists
echo "Ensuring namespace ${NAMESPACE} exists..."
kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

# Apply base manifests
echo "Applying base namespace / RBAC / storage manifests..."
# Update namespace in manifests
sed -i.bak "s/jupyterhub-test/${NAMESPACE}/g" infra/namespaces.yaml infra/storage/pvc-home.yaml infra/network/ingress.yaml 2>/dev/null || true

kubectl apply -f infra/namespaces.yaml
kubectl apply -f infra/storage/pvc-home.yaml

# Add JupyterHub Helm repo
echo "Adding JupyterHub Helm repo..."
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart >/dev/null 2>&1 || true
helm repo update jupyterhub

# Deploy JupyterHub
echo "Deploying JupyterHub release ${RELEASE_NAME} into ${NAMESPACE}..."
helm upgrade --install "${RELEASE_NAME}" jupyterhub/jupyterhub \
  --namespace "${NAMESPACE}" \
  --version "${CHART_VERSION}" \
  --values "${VALUES_FILE}" \
  --timeout 10m

# Apply ingress (no TLS - Cloudflare handles it)
echo "Applying ingress..."
kubectl apply -f infra/network/ingress.yaml

# Apply monitoring (optional)
echo "Applying monitoring manifests..."
kubectl apply -f infra/monitoring/servicemonitor.yaml 2>/dev/null || echo "  ServiceMonitor apply failed (Prometheus Operator may not be installed)."

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "JupyterHub should be accessible at:"
echo "  https://${JHUB_HOST}"
echo ""
echo "Wait 1-2 minutes for pods to start, then check status:"
echo "  kubectl get pods -n ${NAMESPACE}"
echo ""
echo "Run smoke tests:"
echo "  export INGRESS_HOST=${JHUB_HOST}"
echo "  ./scripts/smoke_test_v1.sh"
echo ""
echo "View logs:"
echo "  kubectl logs -n ${NAMESPACE} -l component=hub --tail=50"
echo ""

