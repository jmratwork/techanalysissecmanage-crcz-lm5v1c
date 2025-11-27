#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IDS_MODULE_PATH="${REPO_ROOT}/subcase_1c/bips/ids_ml.py"

if [ ! -f "${IDS_MODULE_PATH}" ]; then
    echo "ids_ml.py no encontrado en ${IDS_MODULE_PATH}, no se puede actualizar el modelo" >&2
    exit 1
fi

PYTHONPATH="${REPO_ROOT}" IDS_MODULE_PATH="${IDS_MODULE_PATH}" python3 - <<'PY'
import importlib.util
import os
import pathlib

module_path = pathlib.Path(os.environ["IDS_MODULE_PATH"])
spec = importlib.util.spec_from_file_location("ids_ml", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.train_model()
module.log_sequence("BIPS model retrained via update_bips_model.sh")
print(f"BIPS model updated: {module.MODEL_FILE}")
PY
