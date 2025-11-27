#!/bin/bash
set -euo pipefail

CTI_FEED_URL="${CTI_FEED_URL:-https://misp.internal.example.com/taxii2/collections/indicators/objects}"
CTI_FETCH_INTERVAL="${CTI_FETCH_INTERVAL:-300}"
OUTPUT_DIR="${CTI_FEED_OUTPUT_DIR:-/var/log/misp}"
CTI_OFFLINE="${CTI_OFFLINE:-0}"
export OUTPUT_DIR CTI_OFFLINE

while [[ $# -gt 0 ]]; do
    case "$1" in
        --offline)
            CTI_OFFLINE=1
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

APT_UPDATED=0
apt_update_once() {
    if [ "$APT_UPDATED" -eq 0 ]; then
        export DEBIAN_FRONTEND=noninteractive
        if ! apt-get update -y; then
            echo "$(date) apt-get update failed" >&2
            return 1
        fi
        APT_UPDATED=1
    fi
}

install_deps() {
    if [ "${SKIP_INSTALL:-0}" -eq 1 ]; then
        return
    fi

    if ! command -v curl >/dev/null 2>&1; then
        apt_update_once || return 1
        export DEBIAN_FRONTEND=noninteractive
        if ! apt-get install -y curl; then
            echo "$(date) failed to install curl" >&2
            return 1
        fi
    fi
}

fetch_with_retries() {
    local attempt=1
    local max_attempts=5
    local delay=1
    while [ "$attempt" -le "$max_attempts" ]; do
        if curl -fsSL "$CTI_FEED_URL" -o "${OUTPUT_DIR}/cti_feed.stix"; then
            return 0
        fi
        echo "$(date) curl attempt $attempt failed" >&2
        sleep "$delay"
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done
    echo "$(date) failed to download CTI feed after $max_attempts attempts" >&2
    return 1
}

fetch_loop() {
    mkdir -p "${OUTPUT_DIR}"
    while true; do
        if [ "$CTI_OFFLINE" -eq 1 ]; then
            echo "$(date) offline mode enabled, skipping CTI fetch" >&2
        elif fetch_with_retries; then
            python3 <<'PYEOF' >>"${OUTPUT_DIR}/ingest.log" 2>&1
import json
import sys
import requests
from stix2 import parse
import os
import time

out_dir = os.environ.get("OUTPUT_DIR", ".")
stix_path = os.path.join(out_dir, "cti_feed.stix")
out_path = os.path.join(out_dir, "cti_enriched.json")
offline = os.environ.get("CTI_OFFLINE") == "1"

def get_with_retries(url, max_attempts=5):
    delay = 1
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return r
            print(f"Attempt {attempt} returned status {r.status_code}")
        except Exception as exc:  # noqa: BLE001
            print(f"Attempt {attempt} failed: {exc}")
        time.sleep(delay)
        delay *= 2
    return None

with open(stix_path) as f:
    bundle = parse(f.read())

enriched = []
for obj in getattr(bundle, "objects", []):
    attack_id = next((ref.get("external_id") for ref in obj.get("external_references", []) if ref.get("source_name") == "mitre-attack" and ref.get("external_id")), None)
    if attack_id:
        print(f"Mapped {obj.get('id')} to ATT&CK {attack_id}")
        obj["mitre_attack_id"] = attack_id

    cve_ids = [
        ref.get("external_id")
        for ref in obj.get("external_references", [])
        if ref.get("source_name") == "cve" and ref.get("external_id")
    ]
    if cve_ids and not offline:
        cpes = []
        for cve in cve_ids:
            r = get_with_retries(f"https://cve.circl.lu/api/cve/{cve}")
            if r:
                data = r.json()
                cpe_entries = data.get("cpe") or []
                if cpe_entries:
                    cpes.extend(cpe_entries)
                    print(f"Mapped {cve} to CPE {cpe_entries}")
            else:
                print(f"Failed to map {cve} after retries")
        if cpes:
            obj["cpe"] = cpes
    elif cve_ids and offline:
        print("Offline mode: skipping CVE lookup")

    enriched.append(obj)

with open(out_path, "w") as fh:
    json.dump([o for o in enriched], fh)
PYEOF

            if command -v misp-cli >/dev/null 2>&1; then
                misp-cli ingest "${OUTPUT_DIR}/cti_enriched.json" >>"${OUTPUT_DIR}/ingest.log" 2>&1 || true
            fi
        else
            echo "$(date) skipping ingestion due to download failure" >&2
        fi
        sleep "$CTI_FETCH_INTERVAL"
    done
}

install_deps
fetch_loop
