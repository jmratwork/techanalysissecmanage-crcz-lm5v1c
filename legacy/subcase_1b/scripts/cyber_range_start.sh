#!/bin/bash
set -euo pipefail

RANGE_LOG="${RANGE_LOG:-/var/log/cyber_range/launch.log}"
VULN_PROFILE="${VULN_PROFILE:-baseline}"
COMPOSE_FILE="$(dirname "$0")/../docker-compose.yml"

if ! command -v docker >/dev/null 2>&1; then
    if [ "${ALLOW_NO_DOCKER:-0}" -eq 1 ]; then
        echo "Docker not found; continuing without launching containers." >&2
        exit 0
    fi
    echo "ERROR: docker command not found. Install Docker to run cyber_range_start.sh." >&2
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: Docker Compose plugin is required."
    exit 1
fi

usage() {
    echo "Usage: $0 [--down]"
    echo "Deploy or tear down the cyber range environment using Docker Compose."
}

log() {
    mkdir -p "$(dirname "$RANGE_LOG")"
    echo "$(date) $1" >> "$RANGE_LOG"
}

deploy() {
    log "Launching cyber range with profile $VULN_PROFILE"
    docker compose -f "$COMPOSE_FILE" up -d
}

teardown() {
    log "Stopping cyber range"
    docker compose -f "$COMPOSE_FILE" down
}

case "${1:-up}" in
    --down|down)
        teardown
        ;;
    --help|-h)
        usage
        ;;
    *)
        deploy
        ;;
 esac
