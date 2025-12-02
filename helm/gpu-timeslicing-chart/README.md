# GPU Time-Slicing Helm Chart

A Helm chart to configure NVIDIA GPU time-slicing for multi-user GPU sharing.

## What This Does

Creates a ConfigMap that tells NVIDIA GPU Operator to enable time-slicing:
- 1 physical GPU → N virtual GPUs (configurable)
- Allows N JupyterHub users to share each GPU

## Installation

### Quick Install

```bash
# Install with default settings (4 replicas)
helm install gpu-timeslicing ./gpu-timeslicing-chart

# Follow the instructions in NOTES.txt to complete setup
```

### Custom Replicas

```bash
# Allow 8 users per GPU
helm install gpu-timeslicing ./gpu-timeslicing-chart \
  --set replicas=8
```

### Custom GPU Operator Namespace

```bash
# If GPU Operator is in a different namespace
helm install gpu-timeslicing ./gpu-timeslicing-chart \
  --set gpuOperatorNamespace=nvidia-gpu-operator
```

## What Gets Created

- **ConfigMap** (`time-slicing-config`) in GPU Operator namespace

**Note:** This chart only creates the ConfigMap. You still need to:
1. Patch ClusterPolicy (shown in NOTES.txt after install)
2. Wait for device plugin restart
3. Deploy JupyterHub

## Uninstall

```bash
helm uninstall gpu-timeslicing

# Also revert ClusterPolicy
kubectl patch clusterpolicy/cluster-policy \
  -n gpu-operator --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": ""}}}}'
```

## Why Not Include This in JupyterHub Chart?

- GPU time-slicing is **cluster-wide** configuration
- JupyterHub chart manages **JupyterHub-specific** resources
- Separation of concerns: GPU config vs application deployment

## Alternative: Use Shell Script

If you prefer, use `../setup-gpu-timeslicing.sh` instead:
```bash
cd ..
./setup-gpu-timeslicing.sh
```

The script does the same thing plus automatic verification.

