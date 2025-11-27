#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLAYBOOK_DIR="${REPO_ROOT}/subcase_1c/playbooks"
VALIDATOR="${REPO_ROOT}/subcase_1c/scripts/validate_playbooks.py"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-chore: update CACAO playbooks}"

if [ ! -d "${PLAYBOOK_DIR}" ]; then
    echo "Directorio de playbooks no encontrado en ${PLAYBOOK_DIR}" >&2
    exit 1
fi

if [ -f "${VALIDATOR}" ]; then
    PYTHONPATH="${REPO_ROOT}" python3 "${VALIDATOR}"
fi

if ! command -v git >/dev/null 2>&1; then
    echo "git no está disponible en la ruta" >&2
    exit 1
fi

if git -C "${REPO_ROOT}" diff --quiet -- "${PLAYBOOK_DIR}"; then
    echo "No hay cambios en los playbooks para versionar"
    exit 0
fi

git -C "${REPO_ROOT}" add "${PLAYBOOK_DIR}"
if git -C "${REPO_ROOT}" commit -m "${COMMIT_MESSAGE}" >/dev/null 2>&1; then
    echo "Playbooks versionados con el mensaje: ${COMMIT_MESSAGE}"
else
    echo "No se pudo crear el commit para los playbooks" >&2
    exit 1
fi
