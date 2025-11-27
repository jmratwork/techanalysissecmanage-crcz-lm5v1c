# Provisioning Subcase 1b Packages

This directory contains example automation for provisioning the subcase 1b sandbox. The NG-SOC
components are distributed through a private APT repository. Each host installs the required
package from this repository, or alternatively, container images can be used.

## Package locations

| Component | Deb package URL | Container image |
|-----------|-----------------|-----------------|
| BIPS | https://example.com/apt/pool/bips/bips-agent.deb | registry.example.com/bips:latest |
| NG-SIEM | https://example.com/apt/pool/ng-siem/ng-siem-server.deb | registry.example.com/ng-siem:latest |
| CICMS | https://example.com/apt/pool/cicms/cicms-server.deb | registry.example.com/cicms:latest |
| NG-SOAR | https://example.com/apt/pool/ng-soar/ng-soar-platform.deb | registry.example.com/ng-soar:latest |

## Adding the private APT repository

The playbook in this folder adds the repository automatically, but manual setup can be performed
as follows:

```bash
echo 'deb [trusted=yes] https://example.com/apt stable main' | \
  sudo tee /etc/apt/sources.list.d/ngsoc.list
sudo apt-get update
sudo apt-get install bips ng-siem cicms ng-soar
```

These packages provide the services required by the BIPS, NG‑SIEM, CICMS and NG‑SOAR hosts during
sandbox provisioning.

## Trainee workstation tool versions

The `build_trainee_workstation.sh` script installs pre‑downloaded packages for the trainee
workstation. The following versions are bundled and verified using SHA256 hashes:

| Tool | Version | Verification command |
|------|---------|---------------------|
| Nmap | 7.93+dfsg1-1 | `nmap --version` |
| GVM  | 25.04.0 | `gvmd --version` |
| OWASP ZAP | 2.16.1 | `zaproxy -version` |
| Caldera | 5.3.0 | `python3 /opt/caldera/server.py --help` |
