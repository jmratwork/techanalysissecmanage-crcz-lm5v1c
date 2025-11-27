#!/bin/bash
set -euo pipefail

LOG_FILE="${LOG_FILE:-/var/log/randomization_platform/start.log}"
EVAL_PROFILE="${EVAL_PROFILE:-default}"
initialize_platform() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$(date) Randomization Evaluation Platform started with profile $EVAL_PROFILE" >> "$LOG_FILE"
}

initialize_platform
