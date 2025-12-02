#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-jupyterhub-test}"
RELEASE_NAME="${RELEASE_NAME:-jhub-v1}"
VALUES_FILE="${VALUES_FILE:-infra/jupyterhub/values-v1.yaml}"
CHART_VERSION="${CHART_VERSION:-2.0.0}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "Ensuring namespace ${NAMESPACE} exists..."
kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

echo "Applying base namespace / RBAC / storage manifests..."
kubectl apply -f infra/namespaces.yaml
kubectl apply -f infra/storage/pvc-home.yaml

echo "Adding JupyterHub Helm repo (if missing)..."
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart >/dev/null 2>&1 || true
helm repo update jupyterhub

echo "Deploying JupyterHub release ${RELEASE_NAME} into ${NAMESPACE}..."
helm upgrade --install "${RELEASE_NAME}" jupyterhub/jupyterhub \
  --namespace "${NAMESPACE}" \
  --version "${CHART_VERSION}" \
  --values "${VALUES_FILE}"

echo "Applying ingress and monitoring manifests..."
kubectl apply -f infra/network/ingress.yaml
kubectl apply -f infra/monitoring/servicemonitor.yaml || echo "ServiceMonitor apply failed (Prometheus Operator may not be installed yet)."

echo "Deployment triggered. Use scripts/smoke_test_v1.sh to verify status."


