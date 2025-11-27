#!/usr/bin/env python3
"""Receive NG-SIEM alerts and create cases in IRIS via REST."""
import os
from typing import Any, Dict

import requests
from flask import Flask, request, jsonify

IRIS_URL = os.getenv("IRIS_URL", "http://localhost:8000/api")
IRIS_API_KEY = os.getenv("IRIS_API_KEY")
PORT = int(os.getenv("BRIDGE_PORT", "8200"))

app = Flask(__name__)


def _build_case(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Map an alert payload to an IRIS case object."""
    return {
        "title": alert.get("rule", alert.get("rule_name", "SIEM Alert")),
        "description": alert.get("description", ""),
        "src_ip": alert.get("source", ""),
        "dest_ip": alert.get("destination", ""),
    }


@app.post("/alert")
def receive_alert() -> "Response":
    alert = request.get_json(force=True)
    case = _build_case(alert)
    headers = {"Authorization": IRIS_API_KEY} if IRIS_API_KEY else {}
    try:
        resp = requests.post(f"{IRIS_URL}/cases", json=case, headers=headers, timeout=10)
        resp.raise_for_status()
        case_id = resp.json().get("id")
        return jsonify({"status": "created", "case_id": case_id})
    except Exception as exc:  # pragma: no cover - logging only
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=PORT)
