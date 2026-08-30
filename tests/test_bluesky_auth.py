"""Tests for BlueSky authentication and retry handling."""

from __future__ import annotations

import logging

import cds_paper_bot


AUTH = {
    "BLUESKY_HANDLE": "cmspapers.bsky.social",
    "BLUESKY_APP_PASSWORD": "test-password",
}


def test_bluesky_auth_retries_transient_network_failure(monkeypatch, caplog):
    """A transient PDS failure should create a fresh client and retry login."""
    clients = []
    sleeps = []

    class FakeClient:
        def __init__(self):
            clients.append(self)

        def login(self, handle, password):
            assert (handle, password) == (
                AUTH["BLUESKY_HANDLE"],
                AUTH["BLUESKY_APP_PASSWORD"],
            )
            if len(clients) == 1:
                raise cds_paper_bot.BlueskyNetworkError()

    monkeypatch.setattr(cds_paper_bot, "BlueskyClient", FakeClient)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", sleeps.append)
    caplog.set_level(logging.INFO)

    client = cds_paper_bot.bluesky_auth(AUTH, retries=3, retry_delay=0.25)

    assert client is clients[1]
    assert len(clients) == 2
    assert sleeps == [0.25]
    assert "Transient BlueSky auth failure (attempt=1/3)" in caplog.text
    assert "Successfully logged into BlueSky" in caplog.text


def test_bluesky_auth_logs_exception_after_retries(monkeypatch, caplog):
    """Exhausted network retries should preserve the exception type and cause."""
    login_attempts = []
    sleeps = []

    class FakeClient:
        def login(self, handle, password):
            login_attempts.append((handle, password))
            try:
                raise TimeoutError("profile endpoint timed out")
            except TimeoutError as timeout:
                raise cds_paper_bot.BlueskyNetworkError() from timeout

    monkeypatch.setattr(cds_paper_bot, "BlueskyClient", FakeClient)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", sleeps.append)
    caplog.set_level(logging.INFO)

    client = cds_paper_bot.bluesky_auth(AUTH, retries=3, retry_delay=0.5)

    assert client is None
    assert len(login_attempts) == 3
    assert sleeps == [0.5, 0.5]
    assert "BlueSky authentication failed after 3 attempts" in caplog.text
    assert "NetworkError" in caplog.text
    assert "profile endpoint timed out" in caplog.text


def test_bluesky_auth_does_not_retry_non_network_failure(monkeypatch, caplog):
    """Credential and response errors should be reported without retries."""
    login_attempts = []

    class FakeClient:
        def login(self, handle, password):
            login_attempts.append((handle, password))
            raise ValueError("invalid session response")

    monkeypatch.setattr(cds_paper_bot, "BlueskyClient", FakeClient)
    monkeypatch.setattr(
        cds_paper_bot.time,
        "sleep",
        lambda _seconds: (_ for _ in ()).throw(AssertionError("unexpected retry")),
    )
    caplog.set_level(logging.INFO)

    client = cds_paper_bot.bluesky_auth(AUTH, retries=3, retry_delay=0.5)

    assert client is None
    assert len(login_attempts) == 1
    assert "failed without retry: ValueError" in caplog.text
    assert "invalid session response" in caplog.text
