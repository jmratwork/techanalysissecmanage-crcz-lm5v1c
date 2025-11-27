#!/bin/bash
set -euo pipefail

LOG_FILE="${LOG_FILE:-/var/log/ng_soar/start.log}"

start_soar() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date) NG-SOAR monitoring activated" >> "$LOG_FILE"
}

start_soar
