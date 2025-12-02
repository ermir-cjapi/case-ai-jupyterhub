# AIV Production Requirements Checklist

This checklist outlines all information and resources needed from AIV IT before deploying JupyterHub to their production environment.

Use this as a communication tool with AIV stakeholders to ensure everything is ready for deployment.

---

## 1. Kubernetes Cluster Access

### 1.1 Cluster Information

- [ ] **Cluster access provided** (kubeconfig file)
- [ ] **Cluster version confirmed** (Kubernetes version: _____________)
- [ ] **Number of nodes:** _____ (CPU nodes), _____ (GPU nodes)
- [ ] **Namespace allocated:** `jupyterhub-prod` (or: _____________)
- [ ] **RBAC permissions granted** for:
  - [ ] Creating pods, services, secrets, configmaps
  - [ ] Creating PVCs (PersistentVolumeClaims)
  - [ ] Creating ingress resources
  - [ ] Creating ServiceMonitors (if using Prometheus Operator)

**Contact:** _______________________________________  
**Documentation:** _________________________________

### 1.2 GPU Nodes

- [ ] **GPU type/model:** ___________________________
- [ ] **Number of GPUs per node:** _________________
- [ ] **NVIDIA device plugin installed:** Yes / No
- [ ] **GPU operator version:** ____________________
- [ ] **Node labels for GPU scheduling:** __________

**Contact:** _______________________________________

---

## 2. Networking & Domain

### 2.1 DNS Configuration

- [ ] **Domain name assigned:** ______________________
  - Recommended: `jupyterhub.aiv.internal` or `ml-platform.aiv.internal`
- [ ] **DNS A record created** pointing to load balancer/ingress IP
- [ ] **DNS propagation verified**

**Contact:** _______________________________________  
**DNS Server:** ____________________________________

### 2.2 Load Balancer / Ingress

- [ ] **Load balancer IP/VIP provided:** ____________
- [ ] **Ingress controller confirmed:**
  - [ ] NGINX Ingress Controller
  - [ ] Traefik
  - [ ] Other: _____________________________________
- [ ] **Ingress class name:** _______________________
- [ ] **TLS termination location:**
  - [ ] At load balancer
  - [ ] At ingress controller
  - [ ] End-to-end to pods

**Contact:** _______________________________________

### 2.3 Network Policies

- [ ] **Network policies required:** Yes / No
- [ ] **Egress restrictions documented**
- [ ] **Ingress restrictions documented**
- [ ] **Firewall rules configured** for:
  - [ ] User access to JupyterHub
  - [ ] JupyterHub to Entra ID (OAuth)
  - [ ] JupyterHub to storage (Ceph/S3)
  - [ ] JupyterHub to GitLab
  - [ ] JupyterHub to Artifactory/registry

**Contact:** _______________________________________

---

## 3. TLS/SSL Certificates

### 3.1 Certificate Details

- [ ] **Corporate CA certificate provided**
- [ ] **Certificate file format:**
  - [ ] PEM (.crt, .pem)
  - [ ] PFX/PKCS12 (.pfx)
  - [ ] Other: _____________________________________
- [ ] **Certificate includes:**
  - [ ] Server certificate
  - [ ] Intermediate CA certificates
  - [ ] Root CA certificate
- [ ] **Private key provided**
- [ ] **Certificate validity period:** _______________
- [ ] **Renewal process documented**

**Certificate Details:**
- Common Name (CN): _______________________________
- Subject Alternative Names (SANs): _______________
- Issuer: __________________________________________

**Contact:** _______________________________________  
**Renewal Schedule:** ______________________________

---

## 4. Authentication & Identity (Entra ID / Active Directory)

### 4.1 Entra ID App Registration

- [ ] **App registration created** in AIV Entra ID tenant
- [ ] **Application (Client) ID:** ___________________
- [ ] **Directory (Tenant) ID:** _____________________
- [ ] **Client Secret generated and provided**
- [ ] **Client Secret expiry date:** _________________
- [ ] **Redirect URI configured:**
  - `https://jupyterhub.aiv.internal/hub/oauth_callback`
- [ ] **API Permissions granted:**
  - [ ] User.Read (Delegated)
  - [ ] GroupMember.Read.All (Delegated or Application)
- [ ] **Admin consent granted**

**Contact:** _______________________________________  
**Entra ID Portal:** https://portal.azure.com

### 4.2 User Groups

- [ ] **Security groups created** in Entra ID/AD:
  - [ ] JupyterHub Users: ___________________________
  - [ ] JupyterHub Admins: __________________________
  - [ ] GPU Users (if restricted): __________________
  - [ ] Other groups: _______________________________

- [ ] **Group Object IDs provided** (if using group-based auth)
- [ ] **User provisioning process documented**

**Contact:** _______________________________________

---

## 5. Container Registry (Artifactory / Jfrog)

### 5.1 Registry Access

- [ ] **Registry URL:** _____________________________
  - Example: `artifactory.aiv.internal`
- [ ] **Repository/project created:** _______________
  - Recommended: `ml-platform` or `jupyterhub`
- [ ] **Credentials provided:**
  - Username: _____________________________________
  - Password/Token: ________________________________
  - Or: Service account credentials
- [ ] **Push permissions granted**
- [ ] **Pull permissions granted**
- [ ] **Kubernetes image pull secret created**

**Registry Details:**
- Full image path example: `artifactory.aiv.internal/ml-platform/base-notebook:v1`

**Contact:** _______________________________________  
**Portal:** ________________________________________

---

## 6. Storage (Ceph / S3)

### 6.1 Storage Class

- [ ] **StorageClass name:** _______________________
  - Examples: `ceph-rbd`, `ceph-s3`, `nfs-client`
- [ ] **Storage backend type:**
  - [ ] Ceph RBD
  - [ ] Ceph S3 (Rados Gateway)
  - [ ] NFS
  - [ ] Other: _____________________________________
- [ ] **Default StorageClass:** Yes / No
- [ ] **Access modes supported:**
  - [ ] ReadWriteOnce (RWO)
  - [ ] ReadWriteMany (RWX)
- [ ] **Provisioner:** _____________________________

**Contact:** _______________________________________

### 6.2 Storage Quotas

- [ ] **Per-user storage quota:** __________________
- [ ] **Shared storage capacity:** __________________
- [ ] **Storage expansion process documented**

**Contact:** _______________________________________

### 6.3 Backup & Recovery

- [ ] **Backup solution in place:** Yes / No
- [ ] **Backup schedule:** ___________________________
- [ ] **Restore procedure documented**
- [ ] **RPO (Recovery Point Objective):** ___________
- [ ] **RTO (Recovery Time Objective):** ____________

**Contact:** _______________________________________

---

## 7. CI/CD & GitLab

### 7.1 GitLab Access

- [ ] **GitLab URL:** _______________________________
  - Example: `https://gitlab.aiv.internal`
- [ ] **Top Level Group created:** __________________
- [ ] **Repository access granted**
- [ ] **Personal Access Token (PAT) provided**
- [ ] **GitLab Runner access:**
  - [ ] Shared runners available
  - [ ] Dedicated runners for ML workloads

**Contact:** _______________________________________

### 7.2 CI/CD Configuration

- [ ] **GitLab CI/CD variables configured:**
  - [ ] `CI_REGISTRY` (Artifactory URL)
  - [ ] `CI_REGISTRY_USER`
  - [ ] `CI_REGISTRY_PASSWORD`
  - [ ] `KUBE_CONFIG` (base64 encoded kubeconfig)
  - [ ] `KUBE_CONTEXT`
- [ ] **Build pipeline permissions granted**
- [ ] **Deployment pipeline permissions granted**

**Contact:** _______________________________________

---

## 8. Monitoring & Observability

### 8.1 Prometheus

- [ ] **Prometheus installed in cluster:** Yes / No
- [ ] **Prometheus Operator installed:** Yes / No
- [ ] **Prometheus namespace:** ______________________
- [ ] **ServiceMonitor support:** Yes / No
- [ ] **Prometheus release name:** __________________
  - Needed for ServiceMonitor labels

**Contact:** _______________________________________

### 8.2 Grafana

- [ ] **Grafana URL:** ______________________________
- [ ] **Grafana access credentials provided**
- [ ] **Data source configured** (Prometheus)
- [ ] **Dashboard import permissions granted**
- [ ] **Folder for JupyterHub dashboards created**

**Contact:** _______________________________________

### 8.3 Alerting

- [ ] **Alerting system in place:**
  - [ ] Prometheus Alertmanager
  - [ ] PagerDuty
  - [ ] Other: _____________________________________
- [ ] **Notification channels configured:**
  - [ ] Email
  - [ ] Slack / Microsoft Teams
  - [ ] Other: _____________________________________
- [ ] **On-call rotation defined:** Yes / No

**Contact:** _______________________________________

---

## 9. IAM & Resource Provisioning

### 9.1 IAM Solution

- [ ] **IAM solution details provided**
- [ ] **API endpoint:** _____________________________
- [ ] **Authentication method:** ____________________
- [ ] **IAM integration required for:**
  - [ ] User workspace provisioning
  - [ ] Resource quota management
  - [ ] Access control
  - [ ] Other: _____________________________________
- [ ] **IAM API documentation provided**

**Contact:** _______________________________________  
**Documentation:** _________________________________

---

## 10. Additional Integrations

### 10.1 Artifact Repository (Backup/Models/Data)

- [ ] **Repository type:**
  - [ ] Jfrog Artifactory
  - [ ] Nexus
  - [ ] S3-compatible storage
  - [ ] Other: _____________________________________
- [ ] **Repository URL:** ___________________________
- [ ] **Access credentials provided**

**Contact:** _______________________________________

### 10.2 Virtual Environment for Coding/IAC

- [ ] **Code server required:** Yes / No
- [ ] **VSCode server integration:** Yes / No
- [ ] **IDE preferences documented**

**Contact:** _______________________________________

### 10.3 Confluence (Documentation)

- [ ] **Confluence space created** for JupyterHub docs
- [ ] **Edit access granted**

**Contact:** _______________________________________

---

## 11. Security & Compliance

### 11.1 Security Requirements

- [ ] **Pod Security Standards documented:**
  - [ ] Privileged
  - [ ] Baseline
  - [ ] Restricted
- [ ] **Container scanning required:** Yes / No
- [ ] **Image signing required:** Yes / No
- [ ] **Secrets management solution:**
  - [ ] Kubernetes Secrets
  - [ ] HashiCorp Vault
  - [ ] Azure Key Vault
  - [ ] Other: _____________________________________

**Contact:** _______________________________________

### 11.2 Compliance

- [ ] **Compliance requirements documented:**
  - [ ] GDPR
  - [ ] HIPAA
  - [ ] SOC 2
  - [ ] Other: _____________________________________
- [ ] **Audit logging requirements:**
  - [ ] User login/logout
  - [ ] Resource access
  - [ ] Data access
- [ ] **Data retention policies:** __________________

**Contact:** _______________________________________

---

## 12. High Availability & Disaster Recovery

### 12.1 HA Configuration

- [ ] **Multi-node deployment required:** Yes / No
- [ ] **Number of JupyterHub replicas:** ____________
- [ ] **Database HA:**
  - [ ] PostgreSQL with replication
  - [ ] Managed database service
  - [ ] Other: _____________________________________
- [ ] **Load balancer HA:** Yes / No

**Contact:** _______________________________________

### 12.2 Disaster Recovery

- [ ] **DR site/cluster available:** Yes / No
- [ ] **Failover procedure documented**
- [ ] **DR testing schedule:** _______________________

**Contact:** _______________________________________

---

## 13. Support & Operations

### 13.1 Operational Support

- [ ] **Operations team identified**
- [ ] **Escalation matrix provided**
- [ ] **SLA requirements documented:**
  - Uptime target: _______________________________
  - Response time: _______________________________
  - Resolution time: _____________________________

**Primary Contact:** ________________________________  
**Backup Contact:** _________________________________  
**Emergency Contact:** ______________________________

### 13.2 Training

- [ ] **Training sessions scheduled** for AIV ops team
- [ ] **Training materials prepared:**
  - [ ] Admin runbook review
  - [ ] Troubleshooting scenarios
  - [ ] Upgrade procedures
  - [ ] User management

**Training Date:** __________________________________

---

## 14. Testing & Validation

### 14.1 Test Environments

- [ ] **Staging/Dev environment available:** Yes / No
- [ ] **Staging environment details:**
  - Cluster: ______________________________________
  - Namespace: ____________________________________
  - URL: __________________________________________

**Contact:** _______________________________________

### 14.2 Test Users

- [ ] **Test users provided** for UAT
- [ ] **Test data available**
- [ ] **Test scenarios documented**

**Test Users:**
1. ________________________________________________
2. ________________________________________________
3. ________________________________________________

---

## 15. Deployment Schedule

### 15.1 Timeline

- [ ] **Deployment window agreed:**
  - Date: __________________________________________
  - Time: __________________________________________
  - Duration: ______________________________________
- [ ] **Change request/ticket created:** ____________
- [ ] **Maintenance notification sent to users**

**Contact:** _______________________________________

### 15.2 Go-Live Criteria

- [ ] All checklist items completed
- [ ] Staging environment tested successfully
- [ ] AIV operations team trained
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested
- [ ] Rollback plan documented
- [ ] User documentation published

---

## Summary Checklist

**Prerequisites:**
- [ ] All sections 1-14 above completed
- [ ] All contacts documented
- [ ] All credentials securely stored
- [ ] All documentation reviewed

**Ready for Deployment:** Yes / No

**Sign-off:**
- Your Team Lead: _________________ Date: _________
- AIV IT Manager: _________________ Date: _________
- AIV Security: ___________________ Date: _________

---

## Notes & Additional Requirements

_Use this space to document any AIV-specific requirements not covered above:_

___________________________________________________________________
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________

---

**Last Updated:** _____________________  
**Updated By:** _______________________  
**Next Review Date:** __________________

