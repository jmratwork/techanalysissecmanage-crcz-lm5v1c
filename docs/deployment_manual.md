# CRCZ/KYPO Deployment Manual

This manual describes how to deploy KYPO training scenarios in this repository. It covers uploading a scenario to the KYPO portal, preparing virtual machines, orchestrating services, and cleaning up afterward.

## Scenario Upload

1. **Validate and package the training**
   ```bash
   kypo training validate training.yaml
   kypo training pack training.yaml
   ```
2. **Upload to KYPO**
   - Using the web portal: create a new training and upload the generated package.
   - Using the CLI:
     ```bash
     kypo training publish training.yaml
     ```
3. **Confirm availability**
   - The training should appear in the KYPO interface and be assignable to exercises.
   - Ensure repository paths referenced in `scenario.yml` files are accessible.

## VM Preparation

1. **Import base images** – Upload or select images for each VM role (e.g., trainee workstation, BIPS, NG‑SIEM).
2. **Update and configure**
   - Apply package updates.
   - Configure network interfaces and hostnames.
   - Create service accounts and SSH keys as required.
3. **Snapshot** – Take a snapshot of each VM after configuration so it can be restored for future exercises.

## Offline Environments

For systems without Internet access, pre-download required packages and modules:

- Copy any necessary `.deb` files to `/opt/offline`. The start scripts for Subcase 1c
  (e.g., `start_soc_services.sh` and `start_cti_component.sh`) will install packages
  from this directory if `apt-get` fails.
- Save PowerShell modules for offline use:
  ```powershell
  Save-Module -Name PowerShellGet,PackageManagement -Path /opt/offline/psmodules
  ```
- Ensure these paths are available on the target machines before running the scenario scripts.

## Service Orchestration

1. **Provision VMs** – Start VMs from the prepared images or snapshots and verify connectivity.
2. **Install Python dependencies** – Before running any scenario scripts, install required packages:
   ```bash
   pip install -r subcase_1b/training_platform/requirements.txt   # for Subcase 1b
   pip install -r subcase_1c/requirements.txt                     # for Subcase 1c
   ```
   The Subcase 1c requirements include the `yara-python` library to enable
   rule-based malware detection.
3. **Launch core services**
   - Start BIPS, NG‑SIEM, CICMS, NG‑SOAR, and related components using the scripts under `subcase_1b/scripts/` or `subcase_1c/scripts/`.
   - If `systemctl` is unavailable, set `DIRECT_START=1` to invoke legacy service scripts.
4. **Validate operation**
   - Confirm ports are listening and dashboards are reachable.
   - Run the scenario‑specific validation steps from the respective guide.

## Teardown

1. **Stop the scenario** from the KYPO dashboard.
2. **Shut down services** using the provided stop scripts or `systemctl stop` commands.
3. **Archive artifacts** such as logs, reports, and captured packets for after‑action review.
4. **Remove temporary resources** including VM instances or storage volumes not needed after the exercise.

## Environment Reset

1. **Revert snapshots** or destroy and recreate VMs to return to a clean state.
2. **Clear persistent data** – Remove leftover logs, temporary files, and database contents.
3. **Reset network configuration** – Delete custom routes or firewall rules applied for the scenario.
4. **Verify baseline** – Ensure no services are running and that the environment matches the initial configuration before the next deployment.

Following these steps ensures consistent deployments and clean teardowns for all scenarios in this repository.
