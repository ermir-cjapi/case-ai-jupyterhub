#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-jupyterhub-test}"
RELEASE_NAME="${RELEASE_NAME:-jhub-v1}"
INGRESS_HOST="${INGRESS_HOST:-jupyterhub-test.example.internal}"

echo "Checking pods in namespace ${NAMESPACE}..."
kubectl get pods -n "${NAMESPACE}"

echo "Waiting for JupyterHub pods to be Ready..."
kubectl wait --for=condition=Ready pod -l app=jupyterhub -n "${NAMESPACE}" --timeout=600s || {
  echo "Pods did not become ready in time."
  exit 1
}

echo "Testing HTTP endpoint via ingress (requires network access from this machine)..."
if command -v curl >/dev/null 2>&1; then
  curl -k "https://${INGRESS_HOST}/hub/health" || echo "Health endpoint not reachable yet."
else
  echo "curl not available; skip HTTP check."
fi

echo "Smoke test completed."


