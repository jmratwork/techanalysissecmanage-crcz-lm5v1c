#!/bin/bash
set -euo pipefail

TARGET="${TARGET:-10.10.0.4}"
LOG_DIR="${LOG_DIR:-/var/log/trainee}"
LOG_FILE="${LOG_FILE:-$LOG_DIR/lab_runner.log}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            TARGET="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--target IP]" >&2
            exit 1
            ;;
    esac
done

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

log() {
    echo "$(date) $1" | tee -a "$LOG_FILE"
}

run_profile() {
    local name="$1"
    local cmd="$2"
    shift 2
    local args=("$@")
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log "$name skipped (missing $cmd)"
        return 0
    fi
    log "Running $name"
    if "$cmd" "${args[@]}" >>"$LOG_FILE" 2>&1; then
        log "$name completed"
    else
        log "$name failed"
    fi
}

run_profile "Reconnaissance sweep" nmap -sV -O "$TARGET"
run_profile "Full TCP scan" nmap -p- "$TARGET"

openvas_xml=$(sed "s/KYPO_SUBNET/$TARGET/" "$(dirname "$0")/../openvas_task_template.xml")
run_profile "OpenVAS scan" gvm-cli socket --xml "$openvas_xml"

tmp_conf=$(mktemp)
sed "s/KYPO_SUBNET/$TARGET/" "$(dirname "$0")/../zap_baseline.conf" > "$tmp_conf"
run_profile "OWASP ZAP baseline scan" zap-baseline.py -t "http://$TARGET" -c "$tmp_conf" -r "$LOG_DIR/zap.html"
rm -f "$tmp_conf"

run_profile "Caldera discovery" caldera run --profile "$(dirname "$0")/../caldera_profiles/discovery.json"

log "Lab run complete"
