"""Result handling utilities and listener service.

This module stores raw result entries coming from the KYPO range and exposes
an optional Flask application that can be used as a lightweight listener
service.  Incoming payloads are appended to ``results.json`` and aggregated
metrics can be calculated for forwarding to other systems such as Open edX.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request

RESULTS_FILE = Path(__file__).with_name("results.json")


def _load() -> List[Dict[str, Any]]:
    """Load all stored results."""
    if RESULTS_FILE.exists():
        try:
            return json.loads(RESULTS_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def append_result(result: Dict[str, Any]) -> None:
    """Append a result entry to the results file."""
    data = _load()
    data.append(result)
    RESULTS_FILE.write_text(json.dumps(data, indent=2))


def aggregate_results(course_id: str, username: str) -> Dict[str, Any]:
    """Return aggregated metrics for the given course and user.

    The current aggregation sums ``score`` values and returns a list of unique
    ``flag`` identifiers that were submitted by the trainee.  The structure is
    intentionally simple so it can be easily extended in the future.
    """

    data = _load()
    relevant = [
        r for r in data if r.get("course_id") == course_id and r.get("username") == username
    ]
    total_score = sum(r.get("score", 0) for r in relevant)
    flags = sorted({r.get("flag") for r in relevant if r.get("flag")})
    return {"score": total_score, "flags": flags}


# ---------------------------------------------------------------------------
# Listener service
app = Flask(__name__)


@app.post("/listener")
def listener() -> Any:
    """Endpoint receiving score/flag data from the KYPO range.

    Expected JSON payload::

        {
            "username": "trainee1",
            "course_id": "course-uuid",
            "score": 10,
            "flag": "flag-1"
        }

    The result is appended to ``results.json`` and aggregated metrics are
    returned in the response.
    """

    data = request.get_json(force=True)
    result = {
        "username": data.get("username"),
        "course_id": data.get("course_id"),
        "score": data.get("score", 0),
        "flag": data.get("flag"),
        "details": data.get("details", {}),
    }
    append_result(result)
    metrics = aggregate_results(result["course_id"], result["username"])
    return jsonify({"status": "recorded", "metrics": metrics})


if __name__ == "__main__":  # pragma: no cover - manual service start
    app.run(host="0.0.0.0", port=6000)
