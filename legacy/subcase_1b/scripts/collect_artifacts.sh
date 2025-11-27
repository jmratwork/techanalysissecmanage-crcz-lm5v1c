#!/bin/bash
set -euo pipefail

OUTPUT="${OUTPUT:-artefacts.zip}"
LOG_DIRS=(
    "/var/log/trainee"
    "/var/log/training_platform"
    "/var/log/cyber_range"
)

collect_artifacts() {
    local files=()
    for dir in "${LOG_DIRS[@]}"; do
        if compgen -G "$dir/*" > /dev/null 2>&1; then
            files+=("$dir"/*)
        fi
    done

    if [ ${#files[@]} -eq 0 ]; then
        echo "No artefacts found" >&2
        exit 1
    fi

    zip -j "$OUTPUT" "${files[@]}" >/dev/null
    echo "Saved artefacts to $OUTPUT"
}

collect_artifacts
