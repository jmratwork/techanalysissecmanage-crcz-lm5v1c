#!/usr/bin/env python3
"""Poll the IRIS API for closed cases and generate post-incident reports.

This script periodically queries the IRIS case management API for cases
whose status is "closed". When a new closed case is found, it runs the
``generate_post_incident_report.sh`` helper and then tags the related MISP
event with ``lessons learned``.

Configuration is handled via environment variables:

``IRIS_URL``            Base URL of the IRIS API (default: http://localhost:8000/api)
``IRIS_API_KEY``        API key for IRIS authentication (optional)
``MISP_URL``            Base URL of the MISP instance (default: http://localhost:8080)
``MISP_API_KEY``        API key for MISP authentication (required for tagging)
``REPORT_SCRIPT``       Path to ``generate_post_incident_report.sh``
                        (default: ../subcase_1c/scripts/generate_post_incident_report.sh)
``POLL_INTERVAL``       Seconds between checks (default: 60)
``STATE_FILE``          File tracking processed case IDs
                        (default: scripts/.iris_processed_cases.json)
``MISP_CA_BUNDLE``      Optional CA bundle path used to validate the MISP TLS
                        certificate. When unset the system trust store is used.

The script stores a JSON list of case IDs it has already handled to avoid
re-running the report for the same case.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Iterable, Set

import requests
from requests import exceptions as requests_exceptions

IRIS_URL = os.getenv("IRIS_URL", "http://localhost:8000/api")
IRIS_API_KEY = os.getenv("IRIS_API_KEY")
MISP_URL = os.getenv("MISP_URL", "http://localhost:8080")
MISP_API_KEY = os.getenv("MISP_API_KEY")
MISP_CA_BUNDLE = os.getenv("MISP_CA_BUNDLE")
REPORT_SCRIPT = os.getenv(
    "REPORT_SCRIPT",
    str(Path(__file__).resolve().parents[1] / "subcase_1c" / "scripts" / "generate_post_incident_report.sh"),
)
UPDATE_BIPS_SCRIPT = os.getenv(
    "UPDATE_BIPS_SCRIPT", str(Path(__file__).resolve().with_name("update_bips_model.sh"))
)
COMMIT_PLAYBOOKS_SCRIPT = os.getenv(
    "COMMIT_PLAYBOOKS_SCRIPT", str(Path(__file__).resolve().with_name("commit_playbooks.sh"))
)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))
STATE_FILE = Path(os.getenv("STATE_FILE", Path(__file__).with_name(".iris_processed_cases.json")))
SEQUENCE_LOG = Path(
    os.getenv("SEQUENCE_LOG", Path(__file__).resolve().parents[1] / "sequence.log")
)


def load_processed() -> Set[str]:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()))
        except Exception:
            return set()
    return set()


def save_processed(case_ids: Iterable[str]) -> None:
    STATE_FILE.write_text(json.dumps(list(case_ids)))


def fetch_closed_cases() -> Iterable[dict]:
    headers = {"Authorization": IRIS_API_KEY} if IRIS_API_KEY else {}
    resp = requests.get(f"{IRIS_URL}/cases", params={"status": "closed"}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Assume API returns a list of case objects
    return data


def run_report() -> None:
    subprocess.run([REPORT_SCRIPT], check=True)


def tag_misp_event(event_id: str) -> None:
    if not MISP_API_KEY:
        raise RuntimeError("MISP_API_KEY is not set; cannot tag event")
    headers = {
        "Authorization": MISP_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {"tag": "lessons learned"}
    request_kwargs = {
        "headers": headers,
        "json": payload,
        "timeout": 30,
    }
    verify_option = MISP_CA_BUNDLE if MISP_CA_BUNDLE else True
    request_kwargs["verify"] = verify_option

    try:
        resp = requests.post(
            f"{MISP_URL}/events/{event_id}/tags/add",
            **request_kwargs,
        )
    except requests_exceptions.SSLError as exc:
        raise RuntimeError(
            "TLS handshake with MISP failed. Verify the certificate or set the "
            "MISP_CA_BUNDLE environment variable with a trusted CA bundle."
        ) from exc
    resp.raise_for_status()


def log_sequence(message: str) -> None:
    """Append a timestamped message to the sequence log."""
    SEQUENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with SEQUENCE_LOG.open("a") as handle:
        handle.write(f"{timestamp} {message}\n")


def run_and_log(script: str, label: str) -> None:
    """Run an external script and log its result."""
    script_path = Path(script)
    if not script_path.exists():
        log_sequence(f"{label} skipped: missing helper at {script_path}")
        return
    try:
        result = subprocess.run([str(script_path)], capture_output=True, text=True, check=True)
        log_sequence(f"{label} succeeded: {result.stdout.strip()}")
    except subprocess.CalledProcessError as exc:  # pragma: no cover - logging only
        log_sequence(f"{label} failed: {exc.stderr.strip()}")


def main() -> None:
    processed = load_processed()
    while True:
        try:
            for case in fetch_closed_cases():
                case_id = str(case.get("id"))
                if case_id in processed:
                    continue
                run_report()
                event_id = case.get("misp_event_id")
                if event_id:
                    try:
                        tag_misp_event(str(event_id))
                    except Exception as exc:  # pragma: no cover - logging only
                        print(f"Failed to tag MISP event {event_id}: {exc}")
                run_and_log(UPDATE_BIPS_SCRIPT, "update_bips_model.sh")
                run_and_log(COMMIT_PLAYBOOKS_SCRIPT, "commit_playbooks.sh")
                processed.add(case_id)
                save_processed(processed)
        except Exception as exc:  # pragma: no cover - logging only
            print(f"Error while polling IRIS: {exc}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
