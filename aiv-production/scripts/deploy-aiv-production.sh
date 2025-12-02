#!/usr/bin/env bash
# Deploy JupyterHub to AIV Production Environment
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

# Load AIV production configuration
if [ -f "aiv-config.env" ]; then
    source aiv-config.env
    echo "✓ Loaded aiv-config.env"
else
    echo "Error: aiv-config.env not found"
    echo "Create it from aiv-config.env.template"
    exit 1
fi

# AIV production settings
export NAMESPACE="${JHUB_NAMESPACE:-jupyterhub-prod}"
export RELEASE_NAME="${RELEASE_NAME:-jhub-production}"
export VALUES_FILE="infra/jupyterhub/values-aiv-production.yaml"
export CHART_VERSION="${CHART_VERSION:-2.0.0}"

echo "=== JupyterHub AIV Production Deployment ==="
echo ""
echo "Environment: AIV Production"
echo "Namespace: ${NAMESPACE}"
echo "Release: ${RELEASE_NAME}"
echo "Domain: ${JHUB_HOST}"
echo "Registry: ${REGISTRY}"
echo "Values: ${VALUES_FILE}"
echo ""

# Verify AIV cluster access
echo "Verifying AIV cluster access..."
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "Error: Cannot access AIV Kubernetes cluster"
    echo "Ensure KUBECONFIG is set correctly"
    exit 1
fi
echo "✓ Cluster access verified"

# Ensure namespace exists
echo "Ensuring namespace ${NAMESPACE} exists..."
kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

# Apply base manifests
echo "Applying base namespace / RBAC manifests..."
kubectl apply -f infra/namespaces.yaml

# Verify required secrets exist
echo "Checking for required secrets..."
MISSING_SECRETS=0

if ! kubectl get secret aiv-corporate-tls -n "${NAMESPACE}" >/dev/null 2>&1; then
    echo "  ⚠ Missing: aiv-corporate-tls (TLS certificate)"
    MISSING_SECRETS=1
fi

if ! kubectl get secret aiv-artifactory-credentials -n "${NAMESPACE}" >/dev/null 2>&1; then
    echo "  ⚠ Missing: aiv-artifactory-credentials (registry credentials)"
    MISSING_SECRETS=1
fi

if ! kubectl get secret entra-id-oauth -n "${NAMESPACE}" >/dev/null 2>&1; then
    echo "  ⚠ Missing: entra-id-oauth (Entra ID credentials)"
    MISSING_SECRETS=1
fi

if [ $MISSING_SECRETS -eq 1 ]; then
    echo ""
    echo "Error: Required secrets are missing. Create them before deploying:"
    echo ""
    echo "# TLS certificate"
    echo "kubectl -n ${NAMESPACE} create secret tls aiv-corporate-tls \\"
    echo "  --cert=/path/to/aiv-corporate.crt \\"
    echo "  --key=/path/to/aiv-corporate.key"
    echo ""
    echo "# Registry credentials"
    echo "kubectl -n ${NAMESPACE} create secret docker-registry aiv-artifactory-credentials \\"
    echo "  --docker-server=${REGISTRY} \\"
    echo "  --docker-username=YOUR_USERNAME \\"
    echo "  --docker-password=YOUR_PASSWORD"
    echo ""
    echo "# Entra ID OAuth"
    echo "kubectl -n ${NAMESPACE} create secret generic entra-id-oauth \\"
    echo "  --from-literal=client-id=YOUR_CLIENT_ID \\"
    echo "  --from-literal=client-secret=YOUR_CLIENT_SECRET \\"
    echo "  --from-literal=tenant-id=YOUR_TENANT_ID"
    echo ""
    exit 1
fi

echo "✓ All required secrets found"

# Apply storage manifests
echo "Applying storage manifests..."
kubectl apply -f infra/storage/

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
  --timeout 15m \
  --wait

# Apply ingress
echo "Applying ingress..."
kubectl apply -f infra/network/ingress.yaml

# Apply monitoring (for AIV Prometheus)
echo "Applying monitoring manifests..."
kubectl apply -f infra/monitoring/servicemonitor.yaml || echo "  ServiceMonitor apply failed (verify Prometheus Operator is installed)."

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "JupyterHub should be accessible at (from AIV network):"
echo "  https://${JHUB_HOST}"
echo ""
echo "Check deployment status:"
echo "  kubectl get pods -n ${NAMESPACE}"
echo "  kubectl get ingress -n ${NAMESPACE}"
echo ""
echo "View hub logs:"
echo "  kubectl logs -n ${NAMESPACE} -l component=hub --tail=100 -f"
echo ""
echo "Monitor rollout:"
echo "  kubectl rollout status deployment/hub -n ${NAMESPACE}"
echo ""
echo "Access Grafana dashboard:"
echo "  ${GRAFANA_URL:-https://grafana.aiv.internal}"
echo ""

