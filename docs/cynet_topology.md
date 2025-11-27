# CYNET Topology Overview

## Subcase 1b
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

## Subcase 1c
- Network segment `malnet` (10.20.0.0/24)
- Virtual machines:
  - **infected_host** – Kali
  - **c2_server** – Debian 11
  - **soc_server** – Debian 11
  - **cti_component** – Debian 11
