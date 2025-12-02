#!/usr/bin/env bash
# Setup Cloudflare Tunnel for JupyterHub Lab Environment
set -euo pipefail

TUNNEL_NAME="${TUNNEL_NAME:-jupyterhub-tunnel}"
JHUB_HOST="${JHUB_HOST:-jupyterhub.yourcompany.com}"
TRAEFIK_SERVICE="${TRAEFIK_SERVICE:-http://192.168.1.93:80}"

echo "=== Cloudflare Tunnel Setup for JupyterHub ==="
echo ""
echo "This script will:"
echo "1. Install cloudflared (if not already installed)"
echo "2. Authenticate with Cloudflare"
echo "3. Create a tunnel named '${TUNNEL_NAME}'"
echo "4. Configure DNS routing"
echo "5. Install as a system service"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Step 1: Install cloudflared
echo ""
echo "Step 1: Installing cloudflared..."
if command -v cloudflared &> /dev/null; then
    echo "✓ cloudflared already installed ($(cloudflared --version))"
else
    echo "Installing cloudflared..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
    echo "✓ cloudflared installed"
fi

# Step 2: Authenticate
echo ""
echo "Step 2: Authenticating with Cloudflare..."
echo "This will open a browser window for authentication."
read -p "Press Enter to continue..."
cloudflared tunnel login
echo "✓ Authentication complete"

# Step 3: Create tunnel
echo ""
echo "Step 3: Creating tunnel '${TUNNEL_NAME}'..."
if cloudflared tunnel list | grep -q "${TUNNEL_NAME}"; then
    echo "⚠ Tunnel '${TUNNEL_NAME}' already exists, skipping creation"
    TUNNEL_ID=$(cloudflared tunnel list | grep "${TUNNEL_NAME}" | awk '{print $1}')
else
    cloudflared tunnel create "${TUNNEL_NAME}"
    TUNNEL_ID=$(cloudflared tunnel list | grep "${TUNNEL_NAME}" | awk '{print $1}')
    echo "✓ Tunnel created with ID: ${TUNNEL_ID}"
fi

# Step 4: Create config file
echo ""
echo "Step 4: Creating tunnel configuration..."
mkdir -p ~/.cloudflared

cat > ~/.cloudflared/config.yml <<EOF
tunnel: ${TUNNEL_NAME}
credentials-file: /home/${USER}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: ${JHUB_HOST}
    service: ${TRAEFIK_SERVICE}
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      keepAliveConnections: 100
  
  - service: http_status:404
EOF

echo "✓ Configuration written to ~/.cloudflared/config.yml"

# Step 5: Route DNS
echo ""
echo "Step 5: Configuring DNS..."
if cloudflared tunnel route dns "${TUNNEL_NAME}" "${JHUB_HOST}" 2>&1 | grep -q "already exists"; then
    echo "⚠ DNS route for ${JHUB_HOST} already exists"
else
    cloudflared tunnel route dns "${TUNNEL_NAME}" "${JHUB_HOST}"
    echo "✓ DNS route created: ${JHUB_HOST} → ${TUNNEL_NAME}"
fi

# Step 6: Test tunnel
echo ""
echo "Step 6: Testing tunnel..."
echo "Starting tunnel in background for 10 seconds..."
timeout 10s cloudflared tunnel run "${TUNNEL_NAME}" &
TUNNEL_PID=$!
sleep 5

if ps -p $TUNNEL_PID > /dev/null; then
    echo "✓ Tunnel started successfully"
    kill $TUNNEL_PID 2>/dev/null || true
    wait $TUNNEL_PID 2>/dev/null || true
else
    echo "⚠ Tunnel test failed, check configuration"
fi

# Step 7: Install as service
echo ""
echo "Step 7: Installing as system service..."
read -p "Install cloudflared as a system service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo cloudflared service install
    sudo systemctl start cloudflared
    sudo systemctl enable cloudflared
    echo "✓ Service installed and started"
    echo ""
    echo "Check status with: sudo systemctl status cloudflared"
else
    echo "Skipped service installation"
    echo ""
    echo "To run manually: cloudflared tunnel run ${TUNNEL_NAME}"
fi

# Summary
echo ""
echo "=== Setup Complete ==="
echo ""
echo "✓ Tunnel Name: ${TUNNEL_NAME}"
echo "✓ Tunnel ID: ${TUNNEL_ID}"
echo "✓ Hostname: ${JHUB_HOST}"
echo "✓ Service: ${TRAEFIK_SERVICE}"
echo ""
echo "Next steps:"
echo "1. Deploy JupyterHub: ./scripts/deploy_jhub_v1.sh"
echo "2. Wait 2-3 minutes for DNS propagation"
echo "3. Access JupyterHub: https://${JHUB_HOST}"
echo ""
echo "Useful commands:"
echo "  - Check tunnel status: sudo systemctl status cloudflared"
echo "  - View tunnel logs: sudo journalctl -u cloudflared -f"
echo "  - List tunnels: cloudflared tunnel list"
echo "  - Stop tunnel: sudo systemctl stop cloudflared"
echo ""

