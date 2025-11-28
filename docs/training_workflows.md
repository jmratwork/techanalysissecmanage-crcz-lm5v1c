# Training Materials and Workflows

This document outlines the theoretical training materials and the workflow expectations for both trainees and instructors operating within the KYPO cyber range environment. The primary scenario focuses on penetration testing and vulnerability assessment training using a Cyber Range environment that mirrors CYNET's network. Participants learn how to discover and document vulnerabilities while following organizational procedures. For operational alert triage in NG‑SOAR tools, refer to the [SOC Analyst Playbook](soc_analyst_playbook.md).

## Theoretical Background

Trainees should familiarize themselves with fundamental concepts in network security, incident response, and malware analysis prior to beginning exercises. Recommended topics include:

- Fundamentals of TCP/IP networking
- Common attack vectors and the kill chain methodology
- Basics of log analysis and threat intelligence
- Overview of vulnerability assessment and penetration testing methodologies

## Registration

Instructors enroll trainees through the KYPO/CyberRangeCZ portal using the
`training.yaml` package produced by the `kypo training pack` workflow described
in the repository root `README.md`. If an LMS is required, import the optional
Open edX course under `open_edx/course/` (zip it per `open_edx/course/README.md`
and upload in Studio). The repository does **not** ship a local LMS or REST
API; progression tracking must be handled by your external platform.

Before invitations go out, bring the Subcase 1c stack online. The SOC baseline
is started with `subcase_1c/scripts/start_soc_services.sh`, which launches BIPS,
NG‑SIEM, NG‑SOAR, CICMS, Decide, and Act while masking sensitive values such as
`MISP_API_KEY`. Threat intelligence ingestion is activated through
`subcase_1c/scripts/start_cti_component.sh`, ensuring MISP and the
`fetch-cti-feed` service are available when trainees join the course. These
steps make NG‑SIEM dashboards (`http://localhost:5602`) and MISP
(`https://localhost:8443`) ready for use before learners begin the lab.

## Lab run

After enrollment, trainees deploy the Subcase 1c lab and exercise NG‑SOC
components directly. The SOC and CTI services remain running from the
registration phase; learners then:

1. Start the C2 beacon traffic with `subcase_1c/scripts/start_c2_server.sh`.
2. Run the benign malware generator on the Windows host using
   `subcase_1c/scripts/benign_malware_simulator.ps1` (or
   `load_malware_simulation.ps1`), which emits beacons to the configured
   URL and drops host artifacts.
3. Inspect telemetry in NG‑SIEM (Kibana), MISP, and BIPS logs under
   `/var/log/bips/`, confirming that Filebeat/Winlogbeat data flows into the
   dashboards and that the generated CTI is linked to alerts.

Scenario assets such as CACAO playbooks and IDS models reside under
`subcase_1c/playbooks/` and `subcase_1c/bips/`, and the smoke test
(`subcase_1c/scripts/smoke_test.sh`) provides an optional end-to-end
verification pass.

## Evaluation

Assessment focuses on whether trainees drive the malware simulation to
observable outcomes and correlate them across the NG‑SOC toolchain. Key
artifacts include exported NG‑SIEM alerts, the correlated MISP event, the
Act/CICMS case created from the IDS alert, and logs captured by
`subcase_1c/scripts/generate_post_incident_report.sh`. This script
aggregates NG‑SIEM, BIPS, and Act logs into `reports/` for instructor
review. Trainees also submit feedback via `subcase_1c/feedback_form.md`, and
instructors can validate automated playbook execution with
`subcase_1c/scripts/validate_playbooks.py` before recording final scores.

Any grading dashboards or LMS score tracking must be provided by your external
platform (for example, Open edX after importing `open_edx/course.zip`). There is
no built-in score listener or `/results` endpoint in this repository; tie-ins to
KYPO leaderboards or third-party LMS systems must be configured outside the
repo using their documented interfaces.

## Trainee Workflow

1. **Scenario Preparation** – Review the scenario description and objectives. Ensure access to required accounts and tools within CyberRangeCZ.
2. **Hands-on Investigation** – Use the training platform to follow course instructions and run semi-automated penetration tests against the Cyber Range.
3. **Reporting** – Compile findings into an assessment report, highlighting discovered vulnerabilities, applicable policy references, and suggested mitigations.

## Instructor Workflow

1. **Monitoring** – Ensure the Cyber Range and training platform are functioning and collect trainee reports.
2. **Evaluation** – Review results, correlate findings where necessary, and provide feedback or remediation guidance.

### Packaging and External Systems

- **KYPO/CyberRangeCZ** – Validate and package training with `kypo training
  validate|pack|publish training.yaml` as outlined in `README.md`. Upload the
  generated archive to your KYPO portal to provision the scenario.
- **Open edX (optional)** – If you want LMS content, zip `open_edx/course/` and
  import it into Open edX Studio. Progress tracking, grading, and any REST
  endpoints are managed by that external LMS.
- **NG‑SOC services** – All runtime integrations referenced in this guide are
  implemented via the scripts under `subcase_1c/scripts/` (for example,
  `start_soc_services.sh`, `start_cti_component.sh`,
  `generate_post_incident_report.sh`, `validate_playbooks.py`, and
  `escalate_incident.sh`). These scripts run against the NG‑SOC components
  deployed in the CYNET/CyberRangeCZ environment.

## Subcase 1c: Malware Handling

For detailed deployment, attack simulation, and validation procedures see the
[Subcase 1c guide](subcase_1c_guide.md).

### Trainee Activities

1. **Lab Deployment** – Start the Subcase 1c lab in the KYPO interface. *Validation:* confirm all virtual machines show a **running** state in the platform dashboard. *Artifacts:* screenshot of the deployment status and exported topology details.
2. **Run Malware Simulator** – Execute the provided malware simulator script inside the designated victim machine. *Validation:* the simulator must output a "simulation completed" message and create traffic logs on the host. *Artifacts:* terminal output log and generated host log files.
3. **Observation in NG-SIEM/NG-SOAR** – Monitor the NG-SIEM/NG-SOAR consoles for alerts generated by the simulator traffic. *Validation:* expected alert identifiers appear in the console with correlated events. *Artifacts:* exported alert report or screenshots of the correlated events.
4. **CTI Ingestion** – Ingest the threat indicators produced by the simulator into the CTI module. *Validation:* the ingestion log shows the indicators accepted and mapped to corresponding alerts. *Artifacts:* CTI feed file and ingestion confirmation log.
5. **Incident Escalation** – After validating an alert, escalate it to DFIR using `scripts/escalate_incident.sh <incident_id> <summary> [severity]`. The script posts the incident to the Decide service, which forwards it to CICMS/DFIR.
6. **Final Evaluation** – Submit findings through the platform’s evaluation form. *Validation:* the platform marks the exercise as completed and records the submission. *Artifacts:* final assessment report and platform submission receipt.

### Instructor Activities

1. **Lab Deployment** – Verify each trainee’s lab deployment using the KYPO control interface. *Validation:* orchestrator logs show successful provisioning of all machines. *Artifacts:* deployment logs and metrics exported from the interface.
2. **Run Malware Simulator** – Monitor simulator execution via remote console or log streaming. *Validation:* simulator run completes without errors and produces expected network activity. *Artifacts:* captured console output and packet capture files.
3. **Observation in NG-SIEM/NG-SOAR** – Confirm alerts appear in NG-SIEM/NG-SOAR and correlate with simulator activity. *Validation:* matching alert IDs and correlation graphs are visible. *Artifacts:* SIEM export files and screenshots of correlation graphs.
4. **CTI Ingestion** – Ensure trainees submit CTI data and that indicators link to SIEM alerts. *Validation:* CTI module logs show successful ingestion and linkage to alert IDs. *Artifacts:* CTI ingestion logs and mapped indicator lists.
5. **Incident Escalation** – Confirm that validated incidents were escalated via the Decide service using the provided script. *Validation:* Decide responds with `status: escalated` and the incident appears in CICMS. *Artifacts:* escalation script output and CICMS incident entry.
6. **Final Evaluation** – Review submitted reports and platform evaluation results. *Validation:* each trainee’s submission status is recorded in the grading dashboard. *Artifacts:* completed grading rubric and evaluation summaries.

These workflows ensure that trainees gain practical experience while instructors maintain oversight within the simulated environment.

## Post-Incident Reporting and Iteration

Run `subcase_1c/scripts/generate_post_incident_report.sh` once evaluations are complete to gather NG‑SIEM, BIPS and Act logs. Review the resulting file in `reports/` following the guidance in `docs/post_incident_process.md` and update playbooks or teaching materials accordingly before the next training cycle.  When the IRIS case poller processes a closed case it also tags the related MISP event, executes `scripts/update_bips_model.sh` to retrain or tune the BIPS model using the shared `subcase_1c/bips/ids_ml.py` helpers, and runs `scripts/commit_playbooks.sh` to validate and version updated CACAO playbooks (creating a Git commit when changes are present).  Results of these actions are appended to `sequence.log` for auditing, and any missing helper scripts are noted without interrupting case processing.

## Log Retrieval and Analysis

Shell commands executed on trainee and target machines are stored in `/var/log/commands.log` and forwarded to the NG‑SIEM by Filebeat. To review activity:

1. Access the NG‑SIEM dashboard (Kibana) and search the `commands` index for specific hosts or time ranges.
2. Correlate command logs with other indexes such as alerts from BIPS or NG‑SOAR to trace trainee actions and resulting events.
3. For offline review, fetch `/var/log/commands.log` from the relevant machine and analyze it with standard tools like `less`, `grep` or timeline analysis utilities.

These logs provide detailed insight into trainee behavior and support both real‑time monitoring and post‑exercise assessments.
