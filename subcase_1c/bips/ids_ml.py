#!/usr/bin/env python3
"""Simple IDS alert processor with ML classification and MISP enrichment.

This module parses Suricata EVE JSON alerts, applies a scikit-learn model to
classify each event as benign or malicious, and updates Suricata rules using a
MISP threat intelligence feed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import joblib
import requests
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

sys.path.append(str(Path(__file__).resolve().parents[2]))
from soc_alerts.notifier import Notifier
from soc_alerts.service import AlertService

MODEL_FILE = Path(__file__).with_name("model.joblib")
DEFAULT_ALERT_FILE = Path("/var/log/suricata/eve.json")
DEFAULT_RULE_FILE = Path("/etc/suricata/rules/misp.rules")
DEFAULT_LOG_FILE = Path("/var/log/bips/alerts.json")
SEQUENCE_LOG = Path("/var/log/bips/sequence.log")

IRIS_URL = os.environ.get("IRIS_URL", "http://localhost:5800/incidents")
MISP_POST_URL = os.environ.get("MISP_POST_URL", "http://localhost:8443/attributes")
ACT_URL = os.environ.get("ACT_URL", "http://localhost:8100/act")
NG_SOAR_URL = os.environ.get("NG_SOAR_URL", "http://localhost:5900/events")


def train_model() -> None:
    """Train a trivial text classifier and persist it."""
    samples = [
        "Exploit attempt detected",
        "Known malicious IP",
        "Normal HTTP traffic",
        "Benign DNS query",
    ]
    labels = [1, 1, 0, 0]  # 1 = malicious, 0 = benign
    vectorizer = CountVectorizer()
    features = vectorizer.fit_transform(samples)
    model = MultinomialNB().fit(features, labels)
    joblib.dump((vectorizer, model), MODEL_FILE)


def load_model():
    """Load the classifier, training it first if necessary."""
    if not MODEL_FILE.exists():
        train_model()
    return joblib.load(MODEL_FILE)


def classify_event(event: dict) -> int:
    """Classify a single Suricata alert event."""
    vectorizer, model = load_model()
    text = event.get("alert", {}).get("signature", "")
    features = vectorizer.transform([text])
    return int(model.predict(features)[0])


def process_alerts(path: Path) -> List[dict]:
    """Process alerts from the given EVE JSON file."""
    results = []
    if not path.exists():
        return results
    with path.open() as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            label = classify_event(event)
            results.append({"event": event, "label": label})
    return results


def write_alerts(alerts: List[dict], log_file: Path = DEFAULT_LOG_FILE) -> None:
    """Write classification results as JSON lines for SIEM ingestion."""
    if not alerts:
        return
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a") as handle:
        for alert in alerts:
            event = alert.get("event", {})
            record = {
                "timestamp": event.get("timestamp"),
                "signature": event.get("alert", {}).get("signature"),
                "src_ip": event.get("src_ip"),
                "dest_ip": event.get("dest_ip"),
                "label": alert.get("label"),
            }
            handle.write(json.dumps(record) + "\n")


def fetch_misp_iocs(url: str) -> Iterable[str]:
    """Fetch indicators from a MISP JSON feed endpoint."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []
    return data.get("iocs", [])


def update_rules_from_misp(url: str, rules_file: Path) -> None:
    """Append MISP IOCs to a Suricata rules file."""
    iocs = fetch_misp_iocs(url)
    if not iocs:
        return
    rules_file.parent.mkdir(parents=True, exist_ok=True)
    with rules_file.open("a") as handle:
        for idx, ioc in enumerate(iocs, start=1):
            rule = (
                f"alert ip {ioc} any -> any any "
                f"(msg:\"MISP IOC {ioc}\"; sid:100000{idx}; rev:1;)\n"
            )
            handle.write(rule)


def log_sequence(message: str) -> None:
    """Append a message to the alert->case->response log."""
    SEQUENCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SEQUENCE_LOG.open("a") as handle:
        handle.write(f"{datetime.utcnow().isoformat()} {message}\n")


def create_case(event: dict) -> None:
    """Open an incident case in IRIS/CICMS."""
    payload = {
        "signature": event.get("alert", {}).get("signature"),
        "src_ip": event.get("src_ip"),
        "dest_ip": event.get("dest_ip"),
        "entry_point": event.get("entry_point"),
        "propagation_method": event.get("propagation_method"),
        "improvements": event.get("improvements"),
    }
    try:
        requests.post(IRIS_URL, json=payload, timeout=5)
        log_sequence(f"case opened for {payload['signature']}")
    except Exception:
        log_sequence("failed to open case")


def push_indicator_to_misp(event: dict) -> None:
    """Send relevant indicators to MISP."""
    indicator = {
        "src_ip": event.get("src_ip"),
        "dest_ip": event.get("dest_ip"),
        "signature": event.get("alert", {}).get("signature"),
    }
    headers = {}
    api_key = os.environ.get("MISP_API_KEY")
    if api_key:
        headers["Authorization"] = api_key
    try:
        requests.post(MISP_POST_URL, json=indicator, headers=headers, timeout=5)
        log_sequence("indicator pushed to MISP")
    except Exception:
        log_sequence("failed to push indicator to MISP")


def annotate_case_with_misp(event: dict) -> None:
    """Query MISP for context and forward it to IRIS and NG-SOAR."""
    indicator = event.get("src_ip")
    if not indicator:
        return
    try:
        resp = requests.get(f"{MISP_POST_URL}?ioc={indicator}", timeout=5)
        resp.raise_for_status()
        context = resp.json()
    except Exception:
        log_sequence("no MISP context available")
        return
    payload = {"indicator": indicator, "context": context}
    try:
        requests.post(f"{IRIS_URL}/annotations", json=payload, timeout=5)
        log_sequence("case annotated with MISP context")
    except Exception:
        log_sequence("failed to annotate case")
    try:
        requests.post(NG_SOAR_URL, json=payload, timeout=5)
    except Exception:
        log_sequence("failed to notify NG-SOAR")


def trigger_mitigation(host: str, event: dict) -> None:
    """Invoke Act to apply the recommended mitigation."""
    payload = {
        "target": host,
        "source": "bips",
        "severity": event.get("alert", {}).get("severity", 1),
    }
    try:
        response = requests.post(ACT_URL, json=payload, timeout=5)
        mitigation = response.json().get("mitigation", "unknown")
        log_sequence(f"mitigation {mitigation} triggered on {host}")
    except Exception:
        log_sequence(f"failed to trigger mitigation for {host}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Process IDS alerts with ML")
    parser.add_argument("--alert-file", type=Path, default=DEFAULT_ALERT_FILE)
    parser.add_argument("--misp-url", default="http://localhost:8443/feed.json")
    parser.add_argument(
        "--update-rules",
        action="store_true",
        help="Fetch MISP feed and append indicators to Suricata rules",
    )
    parser.add_argument(
        "--notify-method",
        choices=["email", "syslog"],
        default="syslog",
        help="Notification channel for SOC alerts",
    )
    parser.add_argument(
        "--email-to",
        help="Destination email when using email notification",
    )
    args = parser.parse_args()

    if args.update_rules:
        update_rules_from_misp(args.misp_url, DEFAULT_RULE_FILE)

    notify_config = {"method": args.notify_method}
    if args.notify_method == "email":
        if not args.email_to:
            parser.error("--email-to required with --notify-method=email")
        notify_config["to"] = args.email_to
    notifier = Notifier(notify_config)
    alert_service = AlertService(notifier)

    results = process_alerts(args.alert_file)
    write_alerts(results)
    for res in results:
        if res.get("label") == 1:
            event = res.get("event", {})
            signature = event.get("alert", {}).get("signature", "malicious")
            host = event.get("dest_ip") or event.get("src_ip") or "unknown"
            alert_service.handle_event("ids_ml", signature, host)
            create_case(event)
            push_indicator_to_misp(event)
            annotate_case_with_misp(event)
            trigger_mitigation(host, event)
        print(json.dumps(res))


if __name__ == "__main__":
    main()
