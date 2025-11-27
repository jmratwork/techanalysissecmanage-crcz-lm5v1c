# Ansible Playbooks for Subcase 1b

These playbooks deploy BIPS, CICMS, NG-SIEM, and NG-SOAR components.

## Variables

- `ngsoar_repo_url`: Base URL for NG-SOAR package repository. Defaults to `https://packages.internal.example.com`. Override in inventory or group vars to use environment-specific repositories.
