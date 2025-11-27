import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from soc_alerts.notifier import Notifier
from soc_alerts.service import AlertService


def test_email_notification(monkeypatch):
    sent = {}

    class DummySMTP:
        def __init__(self, host, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def sendmail(self, from_addr, to_addrs, msg):
            sent["from"] = from_addr
            sent["to"] = to_addrs
            sent["msg"] = msg

    monkeypatch.setattr("smtplib.SMTP", DummySMTP)

    notifier = Notifier({"method": "email", "to": "dest@example.com"})
    service = AlertService(notifier)
    service.handle_event("malware_detection", "malware", "host1")

    assert sent["to"] == ["dest@example.com"]
    assert "malware" in sent["msg"]


def test_syslog_notification(monkeypatch):
    messages = []

    def fake_emit(self, record):
        messages.append(self.format(record))

    monkeypatch.setattr("logging.handlers.SysLogHandler.emit", fake_emit)

    notifier = Notifier({"method": "syslog"})
    service = AlertService(notifier)
    service.handle_event("bips", "intrusion", "host2")

    assert any("intrusion" in m for m in messages)


def test_webhook_notification():
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            received["data"] = json.loads(body.decode())
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):  # noqa: A003
            return

    server = HTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{server.server_port}/"
    notifier = Notifier({"method": "webhook", "url": url})
    service = AlertService(notifier)
    service.handle_event("malware_detection", "malware", "host3")

    server.shutdown()
    thread.join()

    assert received["data"]["alert"].startswith("[")
    assert "malware_detection" in received["data"]["alert"]

