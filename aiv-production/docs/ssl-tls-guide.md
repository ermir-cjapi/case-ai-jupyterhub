# SSL/TLS Setup Guide for JupyterHub

This guide provides detailed instructions for securing your JupyterHub deployment with SSL/TLS certificates.

## Why SSL/TLS is Critical for JupyterHub

1. **OAuth Requires HTTPS**: GitHub OAuth, Entra ID, and other identity providers require HTTPS callback URLs
2. **Data Protection**: Encrypts all traffic including passwords, notebooks, and data
3. **Browser Security**: Modern browsers block insecure features (webcam, microphone, etc.) on HTTP
4. **Compliance**: Most organizations require HTTPS for production services

## Three Approaches (Choose One)

### Option 1: Self-Signed Certificate (Lab/Testing)

**Best for**: Quick setup, internal lab environment, testing

**Pros**: Fast, no external dependencies
**Cons**: Browser warnings, manual trust setup required

#### Steps

**1. Generate the certificate:**

```bash
# Create directory for certificates
mkdir -p certs
cd certs

# Generate private key and certificate (valid for 1 year)
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout jhub.key \
  -out jhub.crt \
  -subj "/C=US/ST=California/L=San Francisco/O=YourOrg/CN=jupyterhub.lab.local"

# Verify the certificate
openssl x509 -in jhub.crt -text -noout
```

**2. Create Kubernetes TLS secret:**

```bash
# Create the secret in your JupyterHub namespace
kubectl -n jupyterhub-test create secret tls jupyterhub-tls \
  --cert=jhub.crt \
  --key=jhub.key

# Verify
kubectl -n jupyterhub-test describe secret jupyterhub-tls
```

**3. Trust the certificate on your machine:**

**Windows:**
```powershell
# Import to Trusted Root Certification Authorities (requires admin)
certutil -addstore -enterprise -f "Root" certs\jhub.crt

# Verify
certutil -store Root | findstr jupyterhub
```

**macOS:**
```bash
# Import to system keychain
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain certs/jhub.crt

# Verify
security find-certificate -a -c jupyterhub.lab.local
```

**Linux:**
```bash
# Ubuntu/Debian
sudo cp certs/jhub.crt /usr/local/share/ca-certificates/jupyterhub.crt
sudo update-ca-certificates

# RHEL/CentOS/Fedora
sudo cp certs/jhub.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust

# Verify
trust list | grep jupyterhub
```

**4. Update ingress manifest:**

Edit `infra/network/ingress.yaml`:

```yaml
spec:
  tls:
    - hosts:
        - jupyterhub.lab.local
      secretName: jupyterhub-tls  # Points to the secret we created
  rules:
    - host: jupyterhub.lab.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: proxy-public
                port:
                  number: 80
```

Apply:

```bash
kubectl apply -f infra/network/ingress.yaml
```

**5. Test:**

```bash
# Test from command line
curl -v https://jupyterhub.lab.local/hub/health

# Open in browser
# Should show green lock icon with no warnings
```

---

### Option 2: Let's Encrypt with cert-manager (Public)

**Best for**: Public-facing JupyterHub, production use, automatic renewal

**Pros**: Free, trusted by all browsers, automatic renewal
**Cons**: Requires public DNS and HTTP/HTTPS reachability from internet

#### Prerequisites

- Your JupyterHub must be accessible from the public internet
- You must have a valid public DNS name (e.g., `jupyterhub.example.com`)
- Port 80 must be reachable for HTTP-01 challenge

#### Steps

**1. Install cert-manager:**

```bash
# Install cert-manager CRDs and controller
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/instance=cert-manager \
  -n cert-manager \
  --timeout=300s

# Verify installation
kubectl get pods -n cert-manager
```

**2. Create a ClusterIssuer:**

Create `certs/letsencrypt-prod-issuer.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    # ACME server URL (production Let's Encrypt)
    server: https://acme-v02.api.letsencrypt.org/directory
    
    # Email for expiration notifications
    email: your-email@example.com  # ⚠️ CHANGE THIS
    
    # Secret to store ACME account private key
    privateKeySecretRef:
      name: letsencrypt-prod-key
    
    # Challenge solver configuration
    solvers:
      # HTTP-01 challenge via ingress
      - http01:
          ingress:
            class: nginx  # Or your ingress class
```

Apply:

```bash
kubectl apply -f certs/letsencrypt-prod-issuer.yaml

# Verify
kubectl get clusterissuer letsencrypt-prod
kubectl describe clusterissuer letsencrypt-prod
```

**3. Create a Certificate resource:**

Create `certs/jupyterhub-certificate.yaml`:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: jupyterhub-cert
  namespace: jupyterhub-test  # ⚠️ Match your JupyterHub namespace
spec:
  # The secret where the certificate will be stored
  secretName: jupyterhub-tls
  
  # Reference to the issuer
  issuerRef:
    kind: ClusterIssuer
    name: letsencrypt-prod
  
  # DNS names for the certificate
  dnsNames:
    - jupyterhub.example.com  # ⚠️ CHANGE to your public DNS name
  
  # Optional: Additional SANs
  # - www.jupyterhub.example.com
  
  # Certificate duration and renewal
  duration: 2160h  # 90 days
  renewBefore: 720h  # Renew 30 days before expiry
```

Apply:

```bash
kubectl apply -f certs/jupyterhub-certificate.yaml

# Watch the certificate being issued
kubectl describe certificate jupyterhub-cert -n jupyterhub-test

# Check certificate request
kubectl get certificaterequest -n jupyterhub-test

# Check ACME challenge
kubectl get challenges -n jupyterhub-test

# Once ready, verify the secret
kubectl get secret jupyterhub-tls -n jupyterhub-test
```

**4. Update ingress to use the certificate:**

Edit `infra/network/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jupyterhub
  namespace: jupyterhub-test
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod  # ⬅️ Add this
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
spec:
  tls:
    - hosts:
        - jupyterhub.example.com  # Your public DNS
      secretName: jupyterhub-tls
  rules:
    - host: jupyterhub.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: proxy-public
                port:
                  number: 80
```

Apply:

```bash
kubectl apply -f infra/network/ingress.yaml
```

**5. Monitor certificate issuance:**

```bash
# Watch the certificate status
kubectl get certificate jupyterhub-cert -n jupyterhub-test -w

# Check logs if there are issues
kubectl logs -n cert-manager -l app=cert-manager --tail=100

# Once status shows "Ready: True", test
curl -v https://jupyterhub.example.com/hub/health
```

#### Troubleshooting Let's Encrypt

**Challenge fails:**
```bash
# Check challenge details
kubectl describe challenge -n jupyterhub-test

# Common issues:
# - DNS not pointing to ingress
# - Port 80 not accessible
# - Ingress controller not configured correctly
```

**Rate limits:**
```bash
# Use staging for testing to avoid rate limits
# Change server URL in ClusterIssuer to:
# server: https://acme-staging-v02.api.letsencrypt.org/directory
```

**Manual renewal:**
```bash
# Delete the secret to force renewal
kubectl delete secret jupyterhub-tls -n jupyterhub-test

# cert-manager will automatically re-issue
```

---

### Option 3: Corporate/Internal CA Certificate

**Best for**: Corporate environments, already have internal PKI, production

**Pros**: Already trusted in your organization, no external dependencies
**Cons**: Requires coordination with IT/security team

#### Steps

**1. Request certificate from your organization:**

Contact your IT/security team and request:
- **Certificate type**: Server/TLS certificate
- **Common Name (CN)**: `jupyterhub.lab.yourcompany.local`
- **Subject Alternative Names (SANs)**: Any additional hostnames
- **Key length**: 2048 or 4096 bit RSA (or ECC P-256)
- **Validity**: 1-3 years (depending on policy)

You'll receive:
- `server.crt` (or `.pem`) – The certificate
- `server.key` – The private key
- `ca-bundle.crt` (optional) – Intermediate CA certificates

**2. Prepare the certificate:**

If you received separate files for the certificate and intermediate CA:

```bash
# Combine server cert and intermediate CA (if needed)
cat server.crt intermediate-ca.crt > fullchain.crt
```

If your organization uses PFX/PKCS12 format, convert it:

```bash
# Extract certificate
openssl pkcs12 -in certificate.pfx -clcerts -nokeys -out server.crt

# Extract private key
openssl pkcs12 -in certificate.pfx -nocerts -nodes -out server.key

# Enter the PFX password when prompted
```

**3. Create Kubernetes TLS secret:**

```bash
kubectl -n jupyterhub-test create secret tls jupyterhub-tls \
  --cert=fullchain.crt \
  --key=server.key

# Verify
kubectl -n jupyterhub-test get secret jupyterhub-tls -o yaml
```

**4. Update ingress (same as other options):**

Edit `infra/network/ingress.yaml` as shown in Option 1, step 4.

**5. Test:**

Since your corporate CA is already trusted on company machines, browsers should show a green lock immediately with no warnings.

```bash
# Test
curl -v https://jupyterhub.lab.yourcompany.local/hub/health

# Check certificate chain
openssl s_client -connect jupyterhub.lab.yourcompany.local:443 -showcerts
```

---

## Verifying SSL/TLS Configuration

### Browser Check

1. Open `https://your-jupyterhub-host` in a browser
2. Click the lock icon in the address bar
3. Verify:
   - Connection is secure
   - Certificate is valid
   - Certificate matches the hostname
   - Certificate is trusted (no warnings)

### Command Line Check

```bash
# Basic connectivity test
curl -v https://jupyterhub.lab.local/hub/health

# Detailed certificate inspection
openssl s_client -connect jupyterhub.lab.local:443 -showcerts

# Check certificate expiration
echo | openssl s_client -connect jupyterhub.lab.local:443 2>/dev/null | \
  openssl x509 -noout -dates

# Validate certificate chain
echo | openssl s_client -connect jupyterhub.lab.local:443 -CAfile ca-bundle.crt
```

### Kubernetes Check

```bash
# Verify TLS secret exists
kubectl get secret jupyterhub-tls -n jupyterhub-test

# View secret contents (base64 encoded)
kubectl get secret jupyterhub-tls -n jupyterhub-test -o yaml

# Decode and view certificate
kubectl get secret jupyterhub-tls -n jupyterhub-test \
  -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout

# Check ingress TLS configuration
kubectl describe ingress jupyterhub -n jupyterhub-test
```

---

## Common Issues and Solutions

### Issue: Browser shows "Your connection is not private" (NET::ERR_CERT_AUTHORITY_INVALID)

**Cause**: Self-signed certificate or certificate not trusted

**Solution**:
- For self-signed certs, add exception in browser or import to system trust store (see Option 1)
- For Let's Encrypt, ensure certificate issued successfully
- For corporate CA, ensure CA root certificate is in system trust store

### Issue: Certificate hostname mismatch

**Cause**: Certificate CN/SAN doesn't match the URL you're accessing

**Solution**:
```bash
# Check what hostnames are in the certificate
openssl x509 -in certs/jhub.crt -text -noout | grep -A1 "Subject Alternative Name"

# Regenerate certificate with correct hostname
```

### Issue: cert-manager certificate stuck in "Pending"

**Cause**: Challenge not completing

**Solution**:
```bash
# Check challenge status
kubectl describe challenge -n jupyterhub-test

# Common fixes:
# 1. Ensure ingress is working: curl http://your-host/.well-known/acme-challenge/test
# 2. Check DNS: nslookup your-host
# 3. Check ingress controller logs: kubectl logs -n ingress-nginx ...
```

### Issue: Certificate expired

**With cert-manager** (auto-renewal):
```bash
# Check certificate status
kubectl describe certificate jupyterhub-cert -n jupyterhub-test

# Force renewal
kubectl delete secret jupyterhub-tls -n jupyterhub-test
# cert-manager will automatically re-issue
```

**Without cert-manager** (manual):
```bash
# Regenerate and replace (for self-signed)
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout jhub.key -out jhub.crt \
  -subj "/CN=jupyterhub.lab.local"

kubectl delete secret jupyterhub-tls -n jupyterhub-test
kubectl create secret tls jupyterhub-tls \
  --cert=jhub.crt --key=jhub.key -n jupyterhub-test
```

---

## Security Best Practices

1. **Never commit private keys to Git**
   - Add `*.key` to `.gitignore`
   - Store keys in Kubernetes secrets only

2. **Use strong key lengths**
   - Minimum 2048-bit RSA
   - Prefer 4096-bit for long-lived certificates
   - Or use ECC P-256 for modern systems

3. **Set appropriate certificate validity**
   - Lab/dev: 1 year is fine
   - Production: Follow your organization's policy (typically 1-2 years)
   - Use cert-manager for automatic renewal

4. **Restrict secret access**
   ```bash
   # Use RBAC to limit who can read TLS secrets
   kubectl create role secret-reader \
     --verb=get,list --resource=secrets \
     --resource-name=jupyterhub-tls -n jupyterhub-test
   ```

5. **Monitor certificate expiration**
   - cert-manager does this automatically
   - For manual certs, set up monitoring/alerts

6. **Use TLS 1.2 or higher**
   - Configure in your ingress controller:
   ```yaml
   # Example for ingress-nginx
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: ingress-nginx-controller
     namespace: ingress-nginx
   data:
     ssl-protocols: "TLSv1.2 TLSv1.3"
     ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:..."
   ```

---

## Summary Table

| Method | Complexity | Cost | Browser Trust | Auto-Renewal | Best For |
|--------|-----------|------|---------------|--------------|----------|
| Self-Signed | Low | Free | ❌ (manual) | ❌ | Lab/Testing |
| Let's Encrypt | Medium | Free | ✅ | ✅ | Public Production |
| Corporate CA | Medium | Varies | ✅ | ❌ | Corporate Production |

---

## Next Steps

After setting up SSL/TLS:

1. **Test authentication flows** – OAuth providers require HTTPS
2. **Update documentation** – Document your certificate renewal process
3. **Set up monitoring** – Alert on certificate expiration (cert-manager helps with this)
4. **Plan for renewal** – Certificates expire; have a process in place

For questions, refer to:
- [DETAILED-SETUP-GUIDE.md](../DETAILED-SETUP-GUIDE.md) – Full deployment guide
- [docs/admin-runbook.md](admin-runbook.md) – Operations guide
- [cert-manager documentation](https://cert-manager.io/docs/) – For Let's Encrypt setup

