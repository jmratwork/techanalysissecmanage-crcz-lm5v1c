#!/usr/bin/env python3
"""Initial MISP sharing configuration for Subcase 1c.

Creates a local sharing group and enables the TLP taxonomy.
The script is idempotent; failures are logged to stderr but do not
halt execution when the group or taxonomy already exist.
"""
import json
import os
import sys
from typing import Any

import requests

MISP_URL = os.getenv("MISP_URL", "http://localhost:8443")
MISP_API_KEY = os.getenv("MISP_API_KEY")

if not MISP_API_KEY:
    print("MISP_API_KEY is not set; aborting sharing setup", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": MISP_API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

session = requests.Session()
session.verify = False  # local demo environment


def _post(path: str, payload: Any | None = None) -> requests.Response:
    url = f"{MISP_URL.rstrip('/')}/{path.lstrip('/')}"
    return session.post(url, headers=HEADERS, json=payload, timeout=10)


def create_local_group() -> None:
    """Create a local sharing group in MISP."""
    group = {
        "name": "Local sharing group",
        "releasability": "Internal",
        "description": "Local sharing group for Subcase 1c",
        "local": True,
    }
    try:
        resp = _post("/sharing_groups/add", group)
        if resp.status_code == 200:
            print("Local sharing group created or already exists.")
        else:
            print(f"Failed to create sharing group: {resp.status_code} {resp.text}", file=sys.stderr)
    except requests.RequestException as exc:
        print(f"Error creating sharing group: {exc}", file=sys.stderr)


def enable_tlp_taxonomy() -> None:
    """Import and enable the TLP taxonomy."""
    for action in ("import", "enable"):
        try:
            resp = _post(f"/taxonomies/{action}/tlp")
            if resp.status_code == 200:
                print(f"TLP taxonomy {action}ed.")
            else:
                print(
                    f"Failed to {action} TLP taxonomy: {resp.status_code} {resp.text}",
                    file=sys.stderr,
                )
        except requests.RequestException as exc:
            print(f"Error during taxonomy {action}: {exc}", file=sys.stderr)


def main() -> None:
    create_local_group()
    enable_tlp_taxonomy()


if __name__ == "__main__":
    main()
