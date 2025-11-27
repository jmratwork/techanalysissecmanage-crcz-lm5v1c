import csv
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests
import jwt


class OpenEdXClient:
    """Client for Open edX LMS and KYPO LTI integrations."""

    def __init__(
        self,
        base_url: str | None = None,
        session_cookie: str | None = None,
        api_token: str | None = None,
    ) -> None:
        # Open edX configuration
        self.base_url = (
            base_url or os.environ.get("OPENEDX_URL", "http://localhost:8000")
        ).rstrip("/")

        # Authentication for Open edX API
        self.session_cookie = session_cookie or os.environ.get(
            "OPENEDX_SESSION_COOKIE"
        )
        self.api_token = api_token or os.environ.get("OPENEDX_API_TOKEN")

        # Gradebook API configuration
        self.gradebook_endpoint = os.environ.get(
            "OPENEDX_GRADEBOOK_ENDPOINT",
            f"{self.base_url}/api/grades/v1/course_grade/{{course_id}}/{{username}}",
        )
        self.gradebook_token = os.environ.get(
            "OPENEDX_GRADEBOOK_TOKEN", self.api_token
        )

        # Keep reference to any errors for diagnostics
        self.errors: list[str] = []
        self.logger = logging.getLogger(__name__)

        # LTI / KYPO configuration. Defaults are suitable for local
        # development and can be overridden via environment variables.
        self.kypo_url = os.environ.get("KYPO_URL", "http://localhost:5000").rstrip("/")
        self.lti_client_id = os.environ.get("LTI_CLIENT_ID", "kypo-consumer")
        self.lti_deployment_id = os.environ.get(
            "LTI_DEPLOYMENT_ID", "kypo-deployment"
        )
        self.lti_launch_url = os.environ.get(
            "KYPO_LTI_LAUNCH_URL", f"{self.kypo_url}/lti/launch"
        )
        # Private key used to sign LTI launch tokens. The variable can
        # contain either the key itself or a path to a file.
        key = os.environ.get("LTI_TOOL_PRIVATE_KEY", "")
        if os.path.exists(key):
            with open(key, "r", encoding="utf-8") as fh:
                key = fh.read()
        self.lti_private_key = key or None

    # ------------------------------------------------------------------
    # Open edX progress reporting
    def update_progress(
        self, username: str, course_id: str, progress: Any
    ) -> tuple[bool, str]:
        """POST progress information to the Open edX courseware API.

        Returns a tuple ``(success, message)``. Any failure will be logged and
        the message returned for further processing by callers.
        """
        payload = {"username": username, "course_id": course_id, "progress": progress}
        url = f"{self.base_url}/courseware/progress"

        headers: dict[str, str] = {}
        cookies: dict[str, str] = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        if self.session_cookie:
            cookies["sessionid"] = self.session_cookie

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers or None,
                cookies=cookies or None,
                timeout=5,
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            message = f"Open edX progress update failed: {exc}"
            self.logger.error(message)
            self.errors.append(message)
            return False, message
        return True, ""

    # ------------------------------------------------------------------
    # Gradebook export
    def push_grade(
        self,
        username: str,
        course_id: str,
        score: Any,
        csv_path: str | None = None,
    ) -> tuple[bool, str]:
        """Append a grade entry to a CSV file for instructor review.

        The default implementation writes ``username``, ``course_id`` and
        ``score`` to ``gradebook.csv`` located next to this module. The path
        can be overridden via ``csv_path``.
        """

        path = Path(csv_path or Path(__file__).with_name("gradebook.csv"))
        try:
            exists = path.exists()
            with path.open("a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                if not exists:
                    writer.writerow(["username", "course_id", "score"])
                writer.writerow([username, course_id, score])
        except OSError as exc:  # pragma: no cover - filesystem errors
            message = f"Grade export failed: {exc}"
            self.logger.error(message)
            self.errors.append(message)
            return False, message
        return True, ""

    # ------------------------------------------------------------------
    # Grade push to LMS
    def push_grade_lms(
        self, username: str, course_id: str, score: Any
    ) -> tuple[bool, str]:
        """Create or update a learner's grade using the Open edX API."""

        payload = {"username": username, "course_id": course_id, "score": score}
        url = self.gradebook_endpoint.format(course_id=course_id, username=username)

        headers: dict[str, str] = {}
        if self.gradebook_token:
            headers["Authorization"] = f"Bearer {self.gradebook_token}"

        try:
            response = requests.post(
                url, json=payload, headers=headers or None, timeout=5
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            message = f"Open edX grade push failed: {exc}"
            self.logger.error(message)
            self.errors.append(message)
            return False, message
        return True, ""

    # ------------------------------------------------------------------
    # KYPO LTI consumer
    def generate_launch_url(self, username: str, lab_id: str) -> str:
        """Create an LTI 1.3 launch URL for the given user and KYPO lab.

        The token is signed locally and appended to the KYPO launch URL.
        Only a subset of the LTI specification is implemented which is
        sufficient for triggering KYPO lab sessions.
        """

        if not self.lti_private_key:
            raise ValueError("LTI_TOOL_PRIVATE_KEY not configured")

        now = int(time.time())
        payload = {
            "iss": self.lti_client_id,
            "aud": self.kypo_url,
            "iat": now,
            "exp": now + 300,  # five minutes
            "nonce": str(uuid.uuid4()),
            "sub": username,
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
            "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": self.lti_deployment_id,
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {"id": lab_id},
            "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": f"{self.kypo_url}/labs/{lab_id}",
        }

        id_token = jwt.encode(payload, self.lti_private_key, algorithm="RS256")
        state = str(uuid.uuid4())
        return f"{self.lti_launch_url}?id_token={id_token}&state={state}"
