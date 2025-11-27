#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the benign malware simulator
BEACON_URL="${BEACON_URL:-http://localhost:5601/beacon}"
if command -v pwsh >/dev/null 2>&1; then
    pwsh -NoLogo -NonInteractive -File "$SCRIPT_DIR/benign_malware_simulator.ps1" -BeaconCount 1 -BeaconIntervalSeconds 1 -BeaconUrl "$BEACON_URL"
elif command -v powershell >/dev/null 2>&1; then
    powershell -NoLogo -NonInteractive -File "$SCRIPT_DIR/benign_malware_simulator.ps1" -BeaconCount 1 -BeaconIntervalSeconds 1 -BeaconUrl "$BEACON_URL"
else
    echo "ERROR: PowerShell is required to run the benign malware simulator." >&2
    exit 1
fi

# Allow some time for services to ingest the events
sleep 5

NG_SIEM_URL="${NG_SIEM_URL:-http://localhost:5601/alerts}"
IRIS_URL="${IRIS_URL:-http://localhost:5800/incidents}"
MISP_URL="${MISP_URL:-http://localhost:8443}"
MISP_API_KEY="${MISP_API_KEY:-}"
MARKER_FILE="${MARKER_FILE:-/tmp/quarantine.marker}"

check_endpoint() {
    local url="$1"
    local pattern="$2"
    if curl -fsS "$url" | grep -qi "$pattern"; then
        return 0
    fi
    return 1
}

echo "Checking NG-SIEM for alerts..."
if ! check_endpoint "$NG_SIEM_URL" "beacon"; then
    echo "ERROR: NG-SIEM alert not found." >&2
    exit 1
fi

echo "Verifying IRIS case creation..."
if ! check_endpoint "$IRIS_URL" "beacon"; then
    echo "ERROR: IRIS case not found." >&2
    exit 1
fi

echo "Ensuring MISP event exists..."
if ! curl -fsS -H "Authorization: $MISP_API_KEY" "$MISP_URL/events" | grep -qi "beacon"; then
    echo "ERROR: MISP event not found." >&2
    exit 1
fi

echo "Confirming NG-SOAR playbook execution..."
if [ ! -f "$MARKER_FILE" ]; then
    echo "ERROR: Quarantine marker file not found: $MARKER_FILE" >&2
    exit 1
fi

echo "Smoke test completed successfully."
