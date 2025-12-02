#!/bin/bash
# Deploy JupyterHub using plain Kubernetes manifests
# Alternative to Helm deployment

set -e

echo "🚀 Deploying JupyterHub with Kubernetes Manifests"
echo "=================================================="

# Check if proxy token is set
if grep -q "CHANGE_ME_RUN_openssl_rand_hex_32" k8s-manifests/02-secrets.yaml; then
    echo "❌ ERROR: You must generate and set the proxy token first!"
    echo ""
    echo "Run this command:"
    echo "  openssl rand -hex 32"
    echo ""
    echo "Then update k8s-manifests/02-secrets.yaml line 11 with the output."
    exit 1
fi

# Check if Azure AD is configured
if grep -q "YOUR_TENANT_ID" k8s-manifests/01-configmap.yaml; then
    echo "⚠️  WARNING: Azure AD credentials not configured"
    echo "   Update k8s-manifests/01-configmap.yaml lines 44-47"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📦 Step 1: Creating namespace..."
kubectl apply -f k8s-manifests/00-namespace.yaml

echo ""
echo "⚙️  Step 2: Creating configuration..."
kubectl apply -f k8s-manifests/01-configmap.yaml

echo ""
echo "🔐 Step 3: Creating secrets..."
kubectl apply -f k8s-manifests/02-secrets.yaml

echo ""
echo "💾 Step 4: Creating storage..."
kubectl apply -f k8s-manifests/03-pvc.yaml

echo ""
echo "🔑 Step 5: Creating RBAC permissions..."
kubectl apply -f k8s-manifests/04-serviceaccount.yaml

echo ""
echo "🧠 Step 6: Deploying Hub..."
kubectl apply -f k8s-manifests/05-hub-deployment.yaml
kubectl apply -f k8s-manifests/06-hub-service.yaml

echo ""
echo "🌐 Step 7: Deploying Proxy..."
kubectl apply -f k8s-manifests/07-proxy-deployment.yaml
kubectl apply -f k8s-manifests/08-proxy-service.yaml

echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=jupyterhub -n jupyterhub-test --timeout=300s

echo ""
echo "✅ JupyterHub deployed successfully!"
echo ""
echo "📊 Current status:"
kubectl get pods,svc -n jupyterhub-test

echo ""
echo "🌍 Access JupyterHub:"
echo "   https://jupyterhub.ccrolabs.com"
echo ""
echo "📝 To view logs:"
echo "   kubectl logs -l component=hub -n jupyterhub-test -f"
echo "   kubectl logs -l component=proxy -n jupyterhub-test -f"
echo ""
echo "🔄 To restart:"
echo "   kubectl rollout restart deployment/hub -n jupyterhub-test"
echo "   kubectl rollout restart deployment/proxy -n jupyterhub-test"

