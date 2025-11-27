#!/bin/bash
set -euo pipefail

LOG_FILE="${LOG_FILE:-/var/log/cicms/start.log}"

start_cicms() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date) CICMS service started" >> "$LOG_FILE"
}

start_cicms
