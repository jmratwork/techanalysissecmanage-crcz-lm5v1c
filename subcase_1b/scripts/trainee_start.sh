#!/bin/bash
set -euo pipefail

TARGET="${TARGET:-10.10.0.4}"
SCAN_LOG="${SCAN_LOG:-/var/log/trainee/scans.log}"
INGEST_URL="${INGEST_URL:-http://localhost:5000/scan}"
SERVICE_DIR="$(dirname "$0")/../training_platform"
CLI="python3 $SERVICE_DIR/cli.py"
TRAINEE="${TRAINEE:-trainee}"
PASSWORD="${PASSWORD:-changeme}"
COURSE_ID="${COURSE_ID:-}"
CALDERA_SERVER="${CALDERA_SERVER:-http://localhost:8888}"
CALDERA_API_KEY="${CALDERA_API_KEY:-changeme}"

# fail fast if insecure default credentials are used
if [ "$PASSWORD" = "changeme" ]; then
    echo "ERROR: Set PASSWORD to a non-default value before running trainee_start.sh" >&2
    exit 1
fi
if [ "$CALDERA_API_KEY" = "changeme" ]; then
    echo "ERROR: Set CALDERA_API_KEY to a non-default value before running trainee_start.sh" >&2
    exit 1
fi

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
    local apt_missing=()
    local snap_missing=()
    command -v nmap >/dev/null 2>&1 || apt_missing+=(nmap)
    command -v jq >/dev/null 2>&1 || apt_missing+=(jq)
    command -v gvm-script >/dev/null 2>&1 || apt_missing+=(gvm)
    command -v zaproxy >/dev/null 2>&1 || snap_missing+=(zaproxy)
    if [ ${#apt_missing[@]} -gt 0 ]; then
        apt_update_once || return 1
        export DEBIAN_FRONTEND=noninteractive
        if ! apt-get install -y "${apt_missing[@]}"; then
            echo "$(date) failed to install ${apt_missing[*]}" >&2
            return 1
        fi
    fi
    if [ ${#snap_missing[@]} -gt 0 ]; then
        apt_update_once || return 1
        export DEBIAN_FRONTEND=noninteractive
        if ! command -v snap >/dev/null 2>&1; then
            apt-get install -y snapd
            systemctl enable --now snapd.socket
            ln -s /var/lib/snapd/snap /snap || true
        fi
        snap install "${snap_missing[@]}" --classic
    fi
}

run_recon() {
    if result=$(nmap -sV -O "$TARGET" 2>&1); then
        printf '%s\n' "$result" >> "$SCAN_LOG"
        if echo "$result" | grep -qiE 'running|os details'; then
            echo "$(date) Reconnaissance succeeded against $TARGET" >> "$SCAN_LOG"
        else
            echo "$(date) Reconnaissance completed but expected fingerprints missing for $TARGET" >> "$SCAN_LOG"
        fi
        send_results "$result"
    else
        echo "$(date) Reconnaissance failed for $TARGET" >> "$SCAN_LOG"
    fi
}

run_nmap_scan() {
    if result=$(nmap -p- "$TARGET" 2>&1); then
        printf '%s\n' "$result" >> "$SCAN_LOG"
        echo "$(date) Completed nmap scan against $TARGET" >> "$SCAN_LOG"
        send_results "$result"
    else
        echo "$(date) Nmap scan failed for $TARGET" >> "$SCAN_LOG"
    fi
}

run_openvas_scan() {
    if command -v gvm-script >/dev/null 2>&1; then
        if result=$(gvm-script --gmp-username admin --gmp-password admin socket /usr/share/gvm/scripts/quick-scan.gmp "$TARGET" 2>&1); then
            printf '%s\n' "$result" >> "$SCAN_LOG"
            echo "$(date) Completed OpenVAS scan against $TARGET" >> "$SCAN_LOG"
            send_results "$result"
        else
            echo "$(date) OpenVAS scan failed for $TARGET" >> "$SCAN_LOG"
        fi
    fi
}

run_zap_scan() {
    if command -v zaproxy >/dev/null 2>&1; then
        report=$(mktemp /tmp/zap-XXXX.html)
        if zaproxy -cmd -quickurl "http://$TARGET" -quickout "$report" >/dev/null 2>&1; then
            echo "$(date) Completed OWASP ZAP scan against $TARGET" >> "$SCAN_LOG"
            send_results "$(cat "$report")"
        else
            echo "$(date) OWASP ZAP scan failed for $TARGET" >> "$SCAN_LOG"
        fi
        rm -f "$report"
    fi
}

run_caldera_operation() {
    if command -v curl >/dev/null 2>&1; then
        agent=$(mktemp /tmp/sandcat-XXXX)
        if curl -sf "$CALDERA_SERVER/file/download/sandcat.go?platform=linux&arch=amd64" -o "$agent"; then
            chmod +x "$agent"
            "$agent" -server "$CALDERA_SERVER" -group red >/tmp/sandcat.log 2>&1 &
            agent_pid=$!
            sleep 5
            op_payload=$(jq -n '{name:"demo-operation"}')
            if curl -s -H "KEY: $CALDERA_API_KEY" -H 'Content-Type: application/json' -d "$op_payload" \
                -X POST "$CALDERA_SERVER/api/v2/operations" > /tmp/caldera-op.log 2>&1 && \
                grep -q '"id"' /tmp/caldera-op.log; then
                echo "$(date) Caldera operation completed" >> "$SCAN_LOG"
                send_results "$(cat /tmp/caldera-op.log)"
            else
                echo "$(date) Caldera operation failed" >> "$SCAN_LOG"
            fi
            kill "$agent_pid" >/dev/null 2>&1 || true
            rm -f "$agent" /tmp/sandcat.log /tmp/caldera-op.log
        else
            echo "$(date) Failed to download Caldera agent" >> "$SCAN_LOG"
        fi
    fi
}

evaluate_results() {
    local pass=1
    grep -q "Reconnaissance succeeded" "$SCAN_LOG" || pass=0
    grep -q "Completed nmap scan" "$SCAN_LOG" || pass=0
    grep -q "Caldera operation" "$SCAN_LOG" || pass=0
    if [ "$pass" -eq 1 ]; then
        echo "$(date) Evaluation passed" >> "$SCAN_LOG"
    else
        echo "$(date) Evaluation failed" >> "$SCAN_LOG"
    fi
}

run_scans() {
    mkdir -p "$(dirname "$SCAN_LOG")"
    run_recon
    run_nmap_scan
    run_openvas_scan
    run_zap_scan
    run_caldera_operation
    evaluate_results
}

send_results() {
    local output="$1"
    if command -v curl >/dev/null 2>&1; then
        payload=$(jq -n --arg target "$TARGET" --arg output "$output" '{target:$target, output:$output}')
        curl -s -H "Content-Type: application/json" -X POST -d "$payload" "$INGEST_URL" >/dev/null 2>&1 || \
            echo "$(date) Failed to send scan results to $INGEST_URL" >> "$SCAN_LOG"
    fi
}

report_progress() {
    $CLI register --username "$TRAINEE" --password "$PASSWORD" --role trainee >/dev/null 2>&1 || true
    TOKEN="$($CLI login --username "$TRAINEE" --password "$PASSWORD")"
    if [ -z "$COURSE_ID" ]; then
        COURSE_ID="$($CLI list-courses --token "$TOKEN" | python3 -c 'import sys,json; data=json.load(sys.stdin); print(next(iter(data.keys()), ""))')"
    fi
    if [ -n "$COURSE_ID" ]; then
        $CLI update-progress --token "$TOKEN" --course-id "$COURSE_ID" --username "$TRAINEE" --progress 100 >/dev/null 2>&1 || true
    fi
}

install_deps
run_scans
report_progress
