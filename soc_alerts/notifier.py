"""Notification utilities for SOC alerts."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from logging.handlers import SysLogHandler
from typing import Dict, Tuple

import requests


class Notifier:
    """Send alerts using email, syslog, or webhook."""

    def __init__(self, config: Dict[str, object]) -> None:
        self.config = config

    def send(self, message: str) -> None:
        method = self.config.get("method")
        if method == "email":
            self._send_email(message)
        elif method == "syslog":
            self._send_syslog(message)
        elif method == "webhook":
            self._send_webhook(message)
        else:
            raise ValueError(f"Unsupported method: {method}")

    # ------------------------------------------------------------------
    # Individual implementations
    def _send_email(self, message: str) -> None:
        smtp_server = self.config.get("smtp_server", "localhost")
        smtp_port = int(self.config.get("smtp_port", 25))
        from_addr = self.config.get("from", "alerts@example.com")
        to_addr = self.config.get("to")
        mime = MIMEText(message)
        mime["Subject"] = self.config.get("subject", "SOC Alert")
        mime["From"] = from_addr
        mime["To"] = to_addr
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(from_addr, [to_addr], mime.as_string())

    def _send_syslog(self, message: str) -> None:
        address: Tuple[str, int] = self.config.get("address", ("localhost", 514))
        logger = logging.getLogger("soc_alerts")
        logger.setLevel(logging.INFO)
        handler = SysLogHandler(address=address)
        logger.addHandler(handler)
        try:
            logger.info(message)
        finally:
            logger.removeHandler(handler)
            handler.close()

    def _send_webhook(self, message: str) -> None:
        url = self.config.get("url")
        headers = {"Content-Type": "application/json"}
        requests.post(url, json={"alert": message}, headers=headers, timeout=5)
