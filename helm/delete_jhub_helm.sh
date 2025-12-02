#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-jupyterhub-test}"
RELEASE_NAME="${RELEASE_NAME:-jhub-v1}"

echo "Uninstalling Helm release ${RELEASE_NAME} from namespace ${NAMESPACE}..."
helm uninstall "${RELEASE_NAME}" -n "${NAMESPACE}" || echo "Helm release not found."

echo "Optionally delete namespace ${NAMESPACE} with:"
echo "  kubectl delete namespace ${NAMESPACE}"


