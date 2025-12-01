# TechAnalysisSecManage CRCZ

This repository provides complete, ready‑to‑deploy instructions for the CyberRangeCZ malware simulation and CTI integration scenario (Subcase 1c) using only the NG‑SOC components from the activity diagram: BIPS, NG‑SIEM, NG‑SOAR, CICMS, etc. It includes file layouts, Ansible roles, and step‑by‑step workflows so instructors and trainees can complete the training without confusion. The materials focus on malware execution, detection, response, and threat‑intelligence sharing across NG‑SIEM, NG‑SOAR, and MISP.

## Prerequisites

- Active account on [CyberRangeCZ](https://www.cyberrange.cz/) with permissions to deploy cyber range scenarios.
- SSH access to the range and ability to run privileged commands.
- Local tools: `git`, `kubectl`, `helm`, and a modern web browser.
- Recommended familiarity with NG-SOC components, including BIPS for behavioral intrusion prevention, NG-SIEM for event correlation, CICMS for incident collaboration, and MISP for CTI sharing.
- The provided startup scripts rely on `systemctl`. If your environment lacks systemd, set `DIRECT_START=1` to attempt starting services with legacy `service` commands or direct scripts.
- Prepare required environment variables such as `LTI_TOOL_PRIVATE_KEY`, `MISP_API_KEY`, and `OPENEDX_URL` as described in [docs/env_variables.md](docs/env_variables.md).

## Deployment on CRCZ

See [deployment manual](docs/deployment_manual.md) for detailed steps including VM preparation, service orchestration, teardown, and environment reset.


1. **Clone the Repository**
   ```bash
   git clone https://github.com/example/techanalysissecmanage-crcz.git
   cd techanalysissecmanage-crcz
   ```
2. **Authenticate to CyberRangeCZ** – Ensure VPN or direct connectivity and log into the portal.
3. **Prepare the Scenario** – Upload required images or scripts (e.g., `subcase_1c/scripts/benign_malware_simulator.ps1`) to the appropriate CRCZ repositories.
4. **Launch the Scenario** – Use the CRCZ interface to create a new exercise and point it to this repository. Configure network ranges and participants as needed.
5. **Monitor the Exercise** – During execution, analysts should track alerts and manage cases using NG-SOC components such as BIPS, NG-SIEM, CICMS, and MISP (for CTI sharing), following the workflow described in [`docs/training_workflows.md`](docs/training_workflows.md) and the deployment/validation steps in [`docs/subcase_1c_guide.md`](docs/subcase_1c_guide.md).

### Malware Simulation and CTI Flow

Subcase 1c focuses on simulating malware behavior and enriching alerts with CTI. The workload includes a benign malware simulator, a command-and-control stub, and MISP for sharing indicators. Walkthroughs for starting the simulator, ingesting observables into NG‑SIEM, and pushing IOCs to MISP are outlined in [`docs/subcase_1c_guide.md`](docs/subcase_1c_guide.md). Use that guide to:

- Run `subcase_1c/scripts/benign_malware_simulator.ps1` on the trainee workstation to generate process, network, and file events.
- Trigger NG‑SOAR playbooks that tag matching alerts with MISP event IDs.
- Validate containment by executing the cleanup actions described in the guide and confirming the updated threat intelligence entries.

### IRIS Case Closure Automation

The repository includes `scripts/iris_case_closed_poll.py`, a helper that
polls an IRIS case-management instance for cases marked as **closed**. When a
newly closed case is discovered it will:

1. Run `subcase_1c/scripts/generate_post_incident_report.sh` to create a
   post-incident report.
2. Tag the associated MISP event with `lessons learned` via the MISP API.

Configuration is handled through environment variables such as `IRIS_URL`,
`IRIS_API_KEY`, `MISP_URL`, and `MISP_API_KEY`. Execute the script with:

```bash
python scripts/iris_case_closed_poll.py
```

The script keeps track of processed case IDs in `scripts/.iris_processed_cases.json`
to avoid duplicate reports.

## Teardown

1. Stop the scenario from the CRCZ dashboard.
2. Remove any temporary resources or virtual machines associated with the exercise.
3. Archive logs and reports for after-action review.
4. Verify that no residual network configurations remain on CyberRangeCZ.

## Troubleshooting and Tool References

- **Connectivity Issues** – Confirm VPN status and that required ports (e.g., 22 for SSH) are open.
- **Scenario Fails to Start** – Ensure all prerequisite images are uploaded and that the repository path is correct.
- **Tool-Specific Logs** – Consult documentation for [BIPS](https://example.com/bips), [NG-SIEM](https://example.com/ng-siem), [CICMS](https://example.com/cicms), and [MISP](https://example.com/misp).

Additional theoretical background and workflow guidance can be found in [`docs/training_workflows.md`](docs/training_workflows.md). For day‑to‑day alert handling, analysts should review the [`SOC Analyst Playbook`](docs/soc_analyst_playbook.md).

## Scenario Guides

![Pilot CYNET](PUC%20-%20CYNET.png)

- [Subcase 1c – Malware Simulation and CTI Integration](docs/subcase_1c_guide.md)
Subcase 1c models a malware incident response exercise, adding a C2 server, a CTI component running MISP, and corresponding services for NG‑SIEM, BIPS, CICMS, and NG‑SOAR. The guide covers deployment, attack simulation, validation, and configuration of detection rules and playbooks.

> **Note:** Subcase 1b penetration-testing materials have been archived under `legacy/` and are out of scope for current deployments. Refer to `legacy/README.md` for details.

## CRCZ/KYPO Training Packaging

After adding or modifying sandbox definitions, you can validate and publish the training module using the `kypo` CLI:

- **Import note:** When uploading sandboxes to the platform, use the Raw link (or local copy from this repo) for `sandboxes/SandboxAgenda/sandbox.yaml`. Do not paste the rendered HTML from GitHub, as it will break parsing.
- **Flavor alignment:** The Terraform backend currently exposes the `medium` flavor; keep `topology.yml` and all sandbox definitions on that flavor to avoid import failures.

#### Flavor troubleshooting

- **List available flavors:** Use the KYPO CLI to query the Terraform backend (for example, `kypo backend show terraform --output json | jq '.flavors[]'`) or check the KYPO portal Infrastructure/Flavors page to see which flavors the backend currently publishes.
- **Match definitions to the backend:** Confirm that the flavor declared in `topology.yml` and in every `flavor:` entry under `sandboxes/SandboxAgenda/sandbox.yaml` exists in the backend list. Mismatches will cause sandbox imports to fail.
- **If `medium` is missing:** Either (a) enable or publish the `medium` flavor on the Terraform backend so it appears in the list, or (b) change all flavor references in both `topology.yml` and the sandbox YAML to a flavor that is present (e.g., `small` or `large`) before running `kypo training validate` and import.

For CyberRangeCZ/KYPO pools, follow this quick checklist when supplying the Sandbox Definition:

1. Open `sandboxes/SandboxAgenda/sandbox.yaml` on GitHub.
2. Click **Raw** and copy that URL (or use the cloned local file path directly).
3. Paste or upload the raw URL/file into the Sandbox Definition form—**avoid** the rendered HTML page URL.
4. Re-run `kypo training validate training.yaml` before uploading to catch formatting errors early.

1. **Validate** the training specification:
   ```bash
   kypo training validate training.yaml
   ```
2. **Pack** the training for distribution:
   ```bash
   kypo training pack training.yaml
   ```
3. **Publish** the package to a KYPO portal:
   ```bash
   kypo training publish training.yaml
   ```
   The publish command expects authentication details appropriate for your CRCZ/KYPO instance.
