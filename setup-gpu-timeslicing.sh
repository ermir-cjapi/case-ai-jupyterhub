#!/bin/bash
# Setup GPU Time-Slicing for Multi-User JupyterHub
# Allows multiple users to share your RTX 5090 simultaneously
#
# What this does:
# - Configures NVIDIA GPU Operator for time-slicing
# - Converts 1 physical GPU → 4 virtual GPUs (configurable)
# - Enables 4 concurrent JupyterHub users instead of 1
#
# Prerequisites:
# - NVIDIA GPU Operator installed (check: kubectl get pods -n gpu-operator)
# - At least 1 NVIDIA GPU in your cluster

set -e

echo "🎮 GPU Time-Slicing Setup for JupyterHub"
echo "=========================================="
echo ""

# Configuration - Change this to adjust users per GPU
REPLICAS=8  # Options: 2, 4, 8, 10, 16
# 2 = 2 users per GPU (50% each when all active)
# 4 = 4 users per GPU (25% each when all active)
# 8 = 8 users per GPU (12.5% each when all active) ⭐ Recommended for RTX 5090
# 10 = 10 users per GPU (10% each when all active)
# 16 = 16 users per GPU (6.25% each when all active)

echo "📋 Configuration:"
echo "   Time-slicing replicas: ${REPLICAS}"
echo "   Max concurrent users per GPU: ${REPLICAS}"
echo ""

# Detect GPUs
echo "🔍 Detecting GPUs in cluster..."
GPU_COUNT=$(kubectl get nodes -o json | jq -r '[.items[].status.capacity."nvidia.com/gpu" // "0"] | map(tonumber) | add')

if [ "$GPU_COUNT" = "0" ] || [ -z "$GPU_COUNT" ]; then
    echo "❌ No GPUs detected in cluster!"
    echo ""
    echo "Possible issues:"
    echo "  1. NVIDIA GPU Operator not installed"
    echo "  2. GPU drivers not loaded"
    echo "  3. Device plugin not running"
    echo ""
    echo "Check GPU operator status:"
    echo "  kubectl get pods -n gpu-operator"
    echo ""
    exit 1
fi

echo "✅ Detected ${GPU_COUNT} GPU(s) in cluster"
echo ""

# Check if gpu-operator namespace exists
if ! kubectl get namespace gpu-operator &> /dev/null; then
    echo "❌ gpu-operator namespace not found!"
    echo "Please install NVIDIA GPU Operator first:"
    echo ""
    echo "  helm repo add nvidia https://helm.ngc.nvidia.com/nvidia"
    echo "  helm repo update"
    echo "  helm install gpu-operator nvidia/gpu-operator \\"
    echo "    --namespace gpu-operator \\"
    echo "    --create-namespace"
    echo ""
    exit 1
fi

echo "📦 Step 1: Creating time-slicing ConfigMap..."

# Create ConfigMap for time-slicing
# Format follows NVIDIA GPU Operator documentation:
# https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    flags:
      migStrategy: none
    sharing:
      timeSlicing:
        resources:
        - name: nvidia.com/gpu
          replicas: ${REPLICAS}
EOF

echo "✅ ConfigMap created/updated"
echo ""

echo "⚙️  Step 2: Configuring GPU Operator to use time-slicing..."

# Check if ClusterPolicy exists
if ! kubectl get clusterpolicy cluster-policy -n gpu-operator &> /dev/null; then
    echo "❌ ClusterPolicy 'cluster-policy' not found!"
    echo "GPU Operator may not be properly installed."
    echo "Check: kubectl get clusterpolicy -A"
    exit 1
fi

# Apply time-slicing configuration to ClusterPolicy
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config", "default": "any"}}}}'

echo "✅ ClusterPolicy patched"
echo ""

echo "⏳ Step 3: Waiting for NVIDIA device plugin to restart..."
echo "   This may take 30-60 seconds..."

# Wait a bit for the patch to take effect
sleep 10

# Wait for rollout
if ! kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n gpu-operator --timeout=120s; then
    echo "⚠️  Rollout status check timed out, but this might be normal."
    echo "   Continuing with verification..."
fi

echo ""
echo "⏳ Waiting for changes to propagate (10 seconds)..."
sleep 10

echo ""
echo "✅ Step 4: Verifying time-slicing configuration..."
echo ""

# Get new GPU count
NEW_GPU_COUNT=$(kubectl get nodes -o json | jq -r '[.items[].status.capacity."nvidia.com/gpu" // "0"] | map(tonumber) | add')

echo "GPU Capacity Check:"
echo "   Before: ${GPU_COUNT} GPU(s)"
echo "   After:  ${NEW_GPU_COUNT} GPU(s)"
echo ""

EXPECTED=$((GPU_COUNT * REPLICAS))

if [ "$NEW_GPU_COUNT" = "$EXPECTED" ]; then
    echo "✅ SUCCESS! Time-slicing is active!"
    echo ""
    echo "🎉 Configuration Summary:"
    echo "   Physical GPUs: ${GPU_COUNT}"
    echo "   Time-slicing replicas: ${REPLICAS}"
    echo "   Virtual GPUs: ${NEW_GPU_COUNT}"
    echo "   Max concurrent JupyterHub users: ${NEW_GPU_COUNT}"
    echo ""
    echo "Performance per user (when all active):"
    echo "   Each user gets ~$((100 / REPLICAS))% of GPU compute"
    echo "   Each user gets 100% when working alone"
    echo ""
elif [ "$NEW_GPU_COUNT" = "$GPU_COUNT" ]; then
    echo "⚠️  WARNING: GPU count unchanged!"
    echo "   Time-slicing may not be active yet."
    echo ""
    echo "Troubleshooting steps:"
    echo "   1. Wait another 30 seconds and check again:"
    echo "      kubectl get nodes -o json | jq '.items[].status.capacity.\"nvidia.com/gpu\"'"
    echo ""
    echo "   2. Check device plugin logs:"
    echo "      kubectl logs -n gpu-operator -l app=nvidia-device-plugin-daemonset --tail=50"
    echo ""
    echo "   3. Restart device plugin manually:"
    echo "      kubectl delete pod -n gpu-operator -l app=nvidia-device-plugin-daemonset"
    echo ""
    echo "   4. Verify ConfigMap:"
    echo "      kubectl get configmap time-slicing-config -n gpu-operator -o yaml"
    echo ""
else
    echo "⚠️  Unexpected GPU count: ${NEW_GPU_COUNT} (expected ${EXPECTED})"
    echo "   Please verify manually."
    echo ""
fi

echo "📊 Detailed Node Information:"
kubectl describe nodes | grep -A 8 "Capacity:" | grep -E "(Name:|nvidia\.com/gpu)"
echo ""

echo "✅ Setup Complete!"
echo ""
echo "Next Steps:"
echo "  1. Deploy/update JupyterHub:"
echo "     cd helm && ./deploy_jhub_helm.sh"
echo ""
echo "  2. Test with multiple users logging in simultaneously"
echo ""
echo "  3. Monitor GPU usage:"
echo "     watch -n 1 nvidia-smi"
echo ""
echo "To change the number of users per GPU:"
echo "  - Edit REPLICAS variable in this script (line 19)"
echo "  - Run this script again"
echo ""
echo "Documentation: helm/GPU-SHARING.md"
echo ""

