# Ansible Playbooks for Subcase 1b (Archived)

> These playbooks are preserved for historical reference only and should not be applied to active training environments.

These playbooks deploy BIPS, CICMS, NG-SIEM, and NG-SOAR components.

## Variables

- `ngsoar_repo_url`: Base URL for NG-SOAR package repository. Defaults to `https://packages.internal.example.com`. Override in inventory or group vars to use environment-specific repositories.
