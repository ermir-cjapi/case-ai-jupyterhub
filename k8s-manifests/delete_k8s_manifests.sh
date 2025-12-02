#!/bin/bash
# Delete JupyterHub deployed via Kubernetes manifests

set -e

echo "🗑️  Deleting JupyterHub"
echo "====================="

echo ""
echo "This will delete:"
echo "  - All JupyterHub pods (hub, proxy)"
echo "  - All user notebook pods"
echo "  - All services"
echo "  - All configurations and secrets"
echo "  - The entire jupyterhub-test namespace"
echo ""
echo "⚠️  WARNING: User data in PVCs will be deleted!"
echo ""
read -p "Are you sure? (yes/NO) " -r
echo

if [[ ! $REPLY == "yes" ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Deleting all resources..."
kubectl delete -f k8s-manifests/

echo ""
echo "✅ JupyterHub deleted successfully!"

