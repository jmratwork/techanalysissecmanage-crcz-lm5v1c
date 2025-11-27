#!/usr/bin/env python3
"""Basic validation for CACAO JSON playbooks."""
import sys
import pathlib
import json

REQUIRED_TOP_LEVEL = {"type", "spec_version", "id", "name", "description", "playbook_types", "workflow"}
REQUIRED_WORKFLOW_KEYS = {"start", "blocks"}
REQUIRED_BLOCK_KEYS = {"type", "description", "action"}


def validate_playbook(path: pathlib.Path) -> None:
    with path.open() as f:
        data = json.load(f)
    missing = REQUIRED_TOP_LEVEL - data.keys()
    if missing:
        raise ValueError(f"missing keys: {', '.join(sorted(missing))}")
    workflow = data["workflow"]
    if REQUIRED_WORKFLOW_KEYS - workflow.keys():
        raise ValueError("workflow missing keys")
    blocks = workflow["blocks"]
    if workflow["start"] not in blocks:
        raise ValueError("start block not defined in blocks")
    for name, block in blocks.items():
        if REQUIRED_BLOCK_KEYS - block.keys():
            raise ValueError(f"block '{name}' missing keys")


def main() -> int:
    base = pathlib.Path(__file__).resolve().parent.parent / "playbooks"
    ok = True
    for file in base.glob("*.json"):
        try:
            validate_playbook(file)
            print(f"{file.name}: OK")
        except Exception as exc:
            ok = False
            print(f"{file.name}: {exc}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
