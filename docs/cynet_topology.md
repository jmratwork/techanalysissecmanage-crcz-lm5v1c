# CYNET Topology Overview

## Subcase 1b (Archived)
- Network segment `training_net` (10.10.0.0/24)
- Virtual machines:
  - **training_platform** – Debian 11
  - **trainee_workstation** – Kali
  - **cyber_range** – Metasploitable2
  - **randomization_platform** – Debian 11
  - **bips** – Debian 11
  - **ng_siem** – Debian 11
  - **cicms** – Debian 11
  - **ng_soar** – Debian 11

> The Subcase 1b topology is retained only in the archived folder at `legacy/sandboxes/topology_subcase_1b.yaml` and should not be used for active deployments.

## Subcase 1c
- Network segment `malnet` (10.20.0.0/24)
- Virtual machines:
  - **infected-host** – Kali
  - **c2-server** – Debian 11
  - **soc-server** – Debian 11
  - **cti-component** – Debian 11
