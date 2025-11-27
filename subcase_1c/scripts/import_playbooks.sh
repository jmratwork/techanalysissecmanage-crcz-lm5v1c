#!/bin/bash
set -euo pipefail

ROASTER_URL="${ROASTER_URL:-http://localhost:${ROASTER_PORT:-8081}}"
SOARCA_URL="${SOARCA_URL:-http://localhost:${SOARCA_PORT:-8082}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYBOOK_DIR="${SCRIPT_DIR}/../playbooks"

if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl not found" >&2
    exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq not found" >&2
    exit 1
fi

for file in "${PLAYBOOK_DIR}"/*.json; do
    [ -e "$file" ] || continue
    echo "Uploading $(basename "$file") to Roaster"
    curl -s -X POST "${ROASTER_URL}/playbooks" \
        -H 'Content-Type: application/json' \
        --data-binary "@${file}" >/dev/null
    pb_id=$(jq -r '.id' "$file" 2>/dev/null || true)
    if [ -n "$pb_id" ] && [ "$pb_id" != "null" ]; then
        echo "Registering ${pb_id} with Soarca"
        curl -s -X POST "${SOARCA_URL}/playbooks/${pb_id}/import" >/dev/null
    fi
done

echo "Playbook import complete."
