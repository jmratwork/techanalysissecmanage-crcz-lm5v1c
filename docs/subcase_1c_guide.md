# Subcase 1c Guide: Malware Simulation and CTI Integration

See [deployment manual](deployment_manual.md) for baseline environment setup and teardown steps before running this scenario. Review [env_variables.md](env_variables.md) and configure required environment variables such as `MISP_API_KEY` before executing scripts.

This guide walks through deploying the Subcase 1c environment, running the
benign malware simulator, and validating that NG‑SOC components respond as
expected.

## Deployment

1. **Install dependencies**
   ```bash
   pip install -r subcase_1c/requirements.txt
   ```
2. **Start SOC services**

   ```bash
   export MISP_API_KEY='your-misp-key'
    sudo MISP_API_KEY="$MISP_API_KEY" subcase_1c/scripts/start_soc_services.sh
    ```

    Launches BIPS, NG‑SIEM, CICMS, NG‑SOAR, Decide, and Act. Port checks rely on
    Bash's `/dev/tcp` and `timeout` rather than external utilities.

    The script masks `MISP_API_KEY` in status messages and logs. Use a
    subshell to inspect only the trailing characters (for example,
    `echo "****${MISP_API_KEY: -4}"`) if you need to compare against the
    expected value without revealing the entire secret.

    The MongoDB instance starts with the admin user `soc_admin` and password
    `soc_password` (override with `MONGO_INITDB_ROOT_USERNAME` and
    `MONGO_INITDB_ROOT_PASSWORD`). Data is persisted to the `cacao-mongo-data`
    Docker volume, and the `oplogMinRetentionHours` setting in
    `subcase_1c/mongod.conf` keeps change history for seven days.

3. **Start CTI component and ingest feeds**

   ```bash
   sudo subcase_1c/scripts/start_cti_component.sh
   ```

   Runs MISP, starts the `fetch-cti-feed` systemd service, and verifies
   NG‑SIEM. Use `CTI_OFFLINE=1` or run the fetch script with `--offline` to
   skip external downloads when network access is unavailable.

4. **Launch the C2 server**

   ```bash
   sudo subcase_1c/scripts/start_c2_server.sh
   ```

5. **Configure malware detection rules**

   YARA rules live in `subcase_1c/malware_detection/rules/`. Add or adjust
   rules in this directory and scan samples with:

   ```bash
   python subcase_1c/malware_detection/scanner.py <sample>
   ```
   The scanner depends on the `yara-python` library provided in the
   Subcase 1c requirements file.

6. **Validate playbooks**

   Act consumes CACAO JSON playbooks from `subcase_1c/playbooks/` for actions
   such as incident response or threat elimination. Validate the playbooks
   before use:

   ```bash
   python subcase_1c/scripts/validate_playbooks.py
   ```

### Sharing policy

`start_cti_component.sh` initializes a local sharing policy for MISP. A
*Local sharing group* limits dissemination to internal participants, and the
`TLP` taxonomy is imported and enabled so that indicators can be tagged with
traffic-light protocol markings. This ensures threat intelligence is scoped to
the local environment and classified consistently.

## IRIS Incident Flow States

The case management system tracks three primary response phases:

- **contain** – initial containment of the incident.
- **eradicate** – removal of malicious artifacts and persistence.
- **recover** – restoration of normal operations.

Transitions into each phase trigger webhooks that send updates to MISP
(``/events/update``) and notify NG‑SOAR (``/act``) so external systems stay
aligned with the incident status.

## Attack Simulation

1. **Execute the malware simulation on a Windows host**

   ```powershell
   $env:BEACON_URL = "http://localhost:5601/beacon"  # optional override
   .\subcase_1c\scripts\benign_malware_simulator.ps1 -BeaconCount 3
   ```

   The beacon URL can also be set directly via the `-BeaconUrl` parameter:

   ```powershell
   .\subcase_1c\scripts\benign_malware_simulator.ps1 -BeaconCount 3 -BeaconUrl http://ng-siem.local/beacon
   ```

   or load via
   [`load_malware_simulation.ps1`](../subcase_1c/scripts/load_malware_simulation.ps1).

2. **Observe telemetry in NG‑SOAR tools**

   Monitor BIPS, NG‑SIEM, CICMS, NG‑SOAR, and MISP for beacons, file drops, and
   CTI correlations.

3. **Verify alerts in NG‑SIEM dashboards**

   - Open Kibana at `http://localhost:5602`.
   - In *Discover*, search for `BenignMalwareSim` to confirm log ingestion from
     Filebeat and Winlogbeat.
   - In the *Security* app, ensure beacon activity from the simulator appears as
     alerts.

4. **Analyst login and triage alerts**

   - Browse to the Kibana dashboard at `http://localhost:5602`.
  - Log in with analyst credentials.
  - Review alerts in the *Security* app and mark them as acknowledged.
  - Acknowledgement can also be recorded via the Act API:

     ```bash
    curl -X POST http://localhost:8100/acknowledge \
         -H 'Content-Type: application/json' \
         -d '{"alert_id": "abc123", "analyst": "analyst"}'
    ```

   Analysts can reference the [SOC Analyst Playbook](soc_analyst_playbook.md) for deeper guidance on navigation, search queries, and alert confirmation.

5. **Verify BIPS alerts**

   Check each BIPS alert to ensure it reflects real activity:

   - Cross-reference the alert indicators with MISP to confirm known threats.
   - Inspect the affected host for related processes, files, or registry changes.
   - Review NG-SIEM and network telemetry to validate event correlation.
   - Compare with benign malware simulator logs to rule out false positives.

6. **Record confirmation in CICMS/Act**

   Analysts document verified alerts in the CICMS case record and update Act
   to mark the alert as confirmed:

   ```bash
   curl -X POST http://localhost:8100/confirm \
        -H 'Content-Type: application/json' \
        -d '{"alert_id": "abc123", "status": "confirmed"}'
   ```

## Validation

1. **Request mitigation guidance and apply response**

   ```bash
   python3 subcase_1c/scripts/apply_mitigation.py 192.0.2.10 --source ng-siem --severity 5
   ```

   The script contacts the Act service, which queries Decide for a
   recommendation and executes the suggested mitigation on the target.

2. **Confirm component status**

   - SOC services accessible on ports 5500 (BIPS), 5601 (NG‑SIEM), 5602 (Kibana
     UI), 5800 (CICMS), 5900 (NG‑SOAR), 8000 (Decide), and 8100 (Act).
   - MISP running on port 8443 with threat feed ingested.
   - C2 server responding on port 9001.
   - Benign malware simulator generates HTTP beacons and file artifacts detected
     by NG‑SOAR components.

3. **Observe incident propagation and containment**

   - Visit IRIS at `http://localhost:5800/incidents` to verify a case was
     created from the IDS alert.
   - In the MISP UI at `http://localhost:8443`, confirm that the indicator
     associated with the alert appears in the event list.
   - Review `/var/log/bips/sequence.log` or Act service logs to ensure the
     recommended mitigation executed automatically in the KYPO environment.

## SOC Analyst Checklist

- **View IRIS cases** – Confirm that each IDS alert generates a case in the incident registry.
- **Verify MISP entries** – Ensure indicators from the simulation appear in the threat feed and are linked to the case.
- **Confirm automated responses** – Check BIPS or Act logs to validate that recommended mitigations executed without manual intervention.

## References

- [`start_soc_services.sh`](../subcase_1c/scripts/start_soc_services.sh)
- [`start_cti_component.sh`](../subcase_1c/scripts/start_cti_component.sh)
- [`bips_start.sh`](../subcase_1c/scripts/bips_start.sh)
- [`fetch-cti-feed.service`](../subcase_1c/ansible/roles/misp/templates/fetch-cti-feed.service.j2)
- [`start_c2_server.sh`](../subcase_1c/scripts/start_c2_server.sh)
- [`apply_mitigation.py`](../subcase_1c/scripts/apply_mitigation.py)
- [`benign_malware_simulator.ps1`](../subcase_1c/scripts/benign_malware_simulator.ps1)
- [`load_malware_simulation.ps1`](../subcase_1c/scripts/load_malware_simulation.ps1)
- [NG‑SOAR components matrix](ngsoar_components_matrix.md)

