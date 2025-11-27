# SOC Analyst Playbook

This playbook guides analysts through NG-SOAR dashboards, typical search queries, and criteria for confirming alerts. It also highlights CACAO playbooks executed through Act.

## Dashboard Navigation

1. **Access Kibana** at `http://localhost:5602` and log in with analyst credentials.
2. Navigate to the **Security** app to view correlated alerts.
3. Use the **Discover** tab for raw event inspection and timeline analysis.
4. Open the **Dashboards** section for visual summaries of BIPS, NG‑SIEM, and CICMS data.

## Search Queries

- `BenignMalwareSim` – confirm logs from the simulator reach NG‑SIEM.
- `event.type:alert and host.name:win-*` – list alerts from Windows hosts.
- `source.ip:192.0.2.* and destination.port:9001` – trace beacon traffic to the C2 server.
- `process.executable:*powershell* and event.action:creation` – identify suspicious PowerShell usage.

## Confirming Alerts

An alert is considered confirmed when:

1. **Correlation** – Indicators match threat intelligence entries in MISP and align with simulator activity.
2. **Host Verification** – Host logs show associated processes, files, or registry changes.
3. **Network Evidence** – NG‑SIEM or packet captures show traffic consistent with the alert.
4. **No Benign Explanation** – Cross‑check with training scripts to rule out expected actions.
5. Record confirmation in CICMS/Act via the appropriate API calls.

## Response Playbooks

| Playbook | Purpose | When to Execute |
|---------|---------|----------------|
| [`response.json`](../subcase_1c/playbooks/response.json) | Isolate a compromised host to prevent spread. | Execute when initial triage shows active compromise or lateral movement. |
| [`elimination.json`](../subcase_1c/playbooks/elimination.json) | Remove malware artifacts and clean quarantine directories. | Run after response to eliminate confirmed malicious components. |
| [`recovery.json`](../subcase_1c/playbooks/recovery.json) | Restore network connectivity and verify critical services. | Apply once elimination is complete and the host is ready to return to production. |

Following this guide ensures analysts can navigate dashboards, perform targeted searches, confirm alerts, and trigger the correct automation playbook during incident response.
