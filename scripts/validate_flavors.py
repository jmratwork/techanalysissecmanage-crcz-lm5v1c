#!/usr/bin/env python3
"""Validate KYPO flavor usage against backend metadata.

This script compares the flavor list exposed by
`kypo backend show terraform --output json | jq '.flavors[]'` with every
`flavor:` entry declared in `topology.yml` and in `sandboxes/**/sandbox.yaml`.
It exits with a non-zero status and a clear error message if discrepancies are
found.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - module availability is environment specific
    sys.stderr.write(
        "PyYAML is required to run this script. Install it with `pip install pyyaml`.\n"
    )
    sys.exit(1)


def extract_flavors(node) -> set[str]:
    """Recursively collect flavor strings from a parsed YAML node."""

    flavors: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "flavor" and isinstance(value, str):
                flavors.add(value)
            flavors.update(extract_flavors(value))
    elif isinstance(node, list):
        for item in node:
            flavors.update(extract_flavors(item))
    return flavors


def load_flavors_from_files(paths: list[Path]) -> set[str]:
    """Load YAML files and return all discovered flavors."""

    discovered: set[str] = set()
    for path in paths:
        if not path.exists():
            sys.stderr.write(f"Expected file not found: {path}\n")
            sys.exit(1)
        try:
            with path.open("r", encoding="utf-8") as handle:
                content = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            sys.stderr.write(f"Failed to parse {path}: {exc}\n")
            sys.exit(1)
        if content is not None:
            discovered.update(extract_flavors(content))
    return discovered


def get_backend_flavors() -> set[str]:
    """Query KYPO backend for flavors via the CLI."""

    command = ["kypo", "backend", "show", "terraform", "--output", "json"]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(
            "Failed to query backend flavors. Ensure the KYPO CLI is installed, "
            "configured, and that `kypo backend show terraform --output json` "
            "succeeds.\n"
        )
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode or 1)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        sys.stderr.write(
            "Unexpected response while parsing backend JSON output. "
            "Confirm the command `kypo backend show terraform --output json` "
            "returns valid JSON.\n"
        )
        sys.stderr.write(f"Raw output: {result.stdout}\n")
        sys.stderr.write(f"Parser error: {exc}\n")
        sys.exit(1)

    flavors = payload.get("flavors")
    if not isinstance(flavors, list):
        sys.stderr.write(
            "Backend response did not include a `flavors` list. "
            "Please check the backend configuration.\n"
        )
        sys.exit(1)

    return {str(item) for item in flavors}


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    definition_files = [repo_root / "topology.yml"]
    definition_files.extend(sorted((repo_root / "sandboxes").rglob("sandbox.yaml")))

    declared_flavors = load_flavors_from_files(definition_files)
    backend_flavors = get_backend_flavors()

    missing_in_backend = sorted(declared_flavors - backend_flavors)
    unused_in_definitions = sorted(backend_flavors - declared_flavors)

    if not missing_in_backend and not unused_in_definitions:
        print("Flavor definitions match backend metadata.")
        print("Backend flavors:", ", ".join(sorted(backend_flavors)) or "<none>")
        print("Declared flavors:", ", ".join(sorted(declared_flavors)) or "<none>")
        return 0

    sys.stderr.write("Flavor discrepancies detected.\n")
    if missing_in_backend:
        sys.stderr.write(
            "Declared flavors missing from backend (adjust definitions or publish these flavors):\n"
        )
        sys.stderr.write("  - " + "\n  - ".join(missing_in_backend) + "\n")
    if unused_in_definitions:
        sys.stderr.write(
            "Backend flavors not referenced in definitions (consider updating sandboxes/topology):\n"
        )
        sys.stderr.write("  - " + "\n  - ".join(unused_in_definitions) + "\n")
    sys.stderr.write(
        "Review the backend list with `kypo backend show terraform --output json | jq '.flavors[]'`.\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
