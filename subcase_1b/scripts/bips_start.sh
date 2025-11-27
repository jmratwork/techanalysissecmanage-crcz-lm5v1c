#!/bin/bash
set -euo pipefail

LOG_FILE="${LOG_FILE:-/var/log/bips/start.log}"

start_bips() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date) BIPS service initialized" >> "$LOG_FILE"
}

start_bips
