"""Tests for the IRIS case closed poll script."""

from unittest import mock

import pytest
import requests

from scripts import iris_case_closed_poll as poll


def _prepare_defaults():
    poll.MISP_API_KEY = "dummy"
    poll.MISP_URL = "https://misp.example"


def test_tag_misp_event_uses_system_trust(monkeypatch):
    _prepare_defaults()
    poll.MISP_CA_BUNDLE = None

    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_post = mock.Mock(return_value=mock_response)
    monkeypatch.setattr(poll.requests, "post", mock_post)

    poll.tag_misp_event("42")

    assert mock_post.call_count == 1
    _, kwargs = mock_post.call_args
    assert kwargs["verify"] is True


def test_tag_misp_event_honours_custom_bundle(monkeypatch):
    _prepare_defaults()
    poll.MISP_CA_BUNDLE = "/tmp/custom-ca.pem"

    mock_response = mock.Mock()
    mock_response.raise_for_status.return_value = None
    mock_post = mock.Mock(return_value=mock_response)
    monkeypatch.setattr(poll.requests, "post", mock_post)

    poll.tag_misp_event("42")

    _, kwargs = mock_post.call_args
    assert kwargs["verify"] == "/tmp/custom-ca.pem"


def test_tag_misp_event_tls_errors_are_clear(monkeypatch):
    _prepare_defaults()
    poll.MISP_CA_BUNDLE = None

    monkeypatch.setattr(
        poll.requests,
        "post",
        mock.Mock(side_effect=requests.exceptions.SSLError("certificate verify failed")),
    )

    with pytest.raises(RuntimeError) as excinfo:
        poll.tag_misp_event("42")

    assert "MISP_CA_BUNDLE" in str(excinfo.value)
    assert "TLS handshake" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
