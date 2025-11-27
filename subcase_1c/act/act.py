from pathlib import Path
from typing import Set

from flask import Flask, request, jsonify
import requests

from soar_engine import SoarEngine

DECIDE_URL = "http://localhost:8000/recommend"
PLAYBOOK_DIR = Path(__file__).resolve().parent.parent / "playbooks"

app = Flask(__name__)
engine = SoarEngine(PLAYBOOK_DIR)

ACKNOWLEDGED_ALERTS: Set[str] = set()


def monitor(target: str) -> None:
    """Default fallback action."""
    print(f"[ACT] Monitoring target: {target}")


ACTIONS = {
    "response": {"func": engine.response, "playbook": "response"},
    "elimination": {"func": engine.elimination, "playbook": "elimination"},
    "recovery": {"func": engine.recovery, "playbook": "recovery"},
    "monitor": {"func": monitor, "playbook": None},
}


def _apply_mitigation(payload: dict) -> dict:
    """Determine and execute mitigation for the given payload."""
    target = payload.get("target", "")
    mitigation = payload.get("mitigation")

    if mitigation is None:
        # Query Decide for recommended mitigation
        response = requests.post(DECIDE_URL, json=payload, timeout=5)
        mitigation = response.json().get("mitigation", "monitor")

    info = ACTIONS.get(mitigation, ACTIONS["monitor"])
    action = info["func"]
    action(target)

    return {
        "mitigation": mitigation,
        "target": target,
        "playbook": info.get("playbook"),
    }


@app.post("/act")
def act() -> "Response":
    """Receive event data, query Decide, and apply recommended mitigation."""
    payload = request.get_json(force=True)
    result = _apply_mitigation(payload)
    return jsonify(result)


@app.post("/alert")
def alert() -> "Response":
    """Webhook endpoint for NG-SIEM alerts."""
    payload = request.get_json(force=True)
    result = _apply_mitigation(payload)
    result["status"] = "received"
    return jsonify(result)


@app.post("/acknowledge")
def acknowledge() -> "Response":
    """Record that an analyst acknowledged an alert."""
    data = request.get_json(force=True)
    alert_id = data.get("alert_id")
    analyst = data.get("analyst", "unknown")
    if not alert_id:
        return jsonify({"status": "error", "message": "alert_id required"}), 400

    ACKNOWLEDGED_ALERTS.add(alert_id)
    print(f"[ACT] Analyst {analyst} acknowledged alert {alert_id}")
    return jsonify({
        "status": "acknowledged",
        "alert_id": alert_id,
        "analyst": analyst,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8100)
