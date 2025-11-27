#!/usr/bin/env bash
# Escalate a confirmed incident to the CICMS/DFIR system via the Decide service.
# Usage: scripts/escalate_incident.sh <incident_id> <summary> [severity]

set -euo pipefail

DECIDE_URL=${DECIDE_URL:-http://localhost:8000/incident}

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <incident_id> <summary> [severity]" >&2
  exit 1
fi

incident_id=$1
summary=$2
severity=${3:-medium}

payload=$(printf '{"id": "%s", "summary": "%s", "severity": "%s"}' "$incident_id" "$summary" "$severity")

curl -sS -H 'Content-Type: application/json' -d "$payload" -X POST "$DECIDE_URL"
