# Post-Incident Process

This document describes the steps to handle the post-incident report generated for Subcase 1c.

## Review the Report
1. Execute `subcase_1c/scripts/generate_post_incident_report.sh` after the incident ends.
2. Locate the timestamped file in the `reports/` directory.
3. Examine the NG‑SIEM, BIPS and Act sections to understand the event timeline and impacts.

## Apply Patches
1. Identify required fixes based on findings in the report.
2. Apply patches to affected systems, validating them in a staging environment first.
3. Record applied patches and verification steps.

## Update Scenario Infrastructure
1. Update playbooks, configurations or images to include the patches.
2. Rebuild or redeploy the lab to ensure changes take effect.
3. Commit infrastructure updates and note them for future iterations.

## Sample Report
The generated report contains sections for input vectors, lateral movement and mitigation times, followed by findings, containment actions and recommendations. A trimmed example is shown below:

```markdown
# Post-Incident Report - SAMPLE

## Summary
### Input Vectors
No relevant entries found.

### Lateral Movements
No relevant entries found.

### Mitigation Times
No relevant entries found.

## Findings
- Placeholder finding.

## Containment Actions
- Placeholder action.

## Recommendations
- Placeholder recommendation.
```

## Instructor Guidance
- Review the **Summary** to ensure trainees identified the initial vector, any lateral movement and how quickly mitigation occurred.
- Discuss the **Findings** and **Containment Actions** with trainees to validate their response steps.
- Use the **Recommendations** section to drive improvements for future iterations of the scenario.
