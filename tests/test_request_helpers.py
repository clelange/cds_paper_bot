"""Test request retry and media download helpers."""

import logging
import os
import sys
from io import BytesIO

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cds_paper_bot  # pylint: disable=wrong-import-position,import-error


class FakeResponse:
    """Minimal response object for request helper tests."""

    def __init__(self, status_code=200, content=b"", raw=None):
        self.status_code = status_code
        self.content = content
        self.raw = raw if raw is not None else BytesIO(content)


class ChunkThenFailRaw:
    """Raw stream that writes one chunk before raising."""

    def __init__(self):
        self.decode_content = False
        self._read_count = 0

    def read(self, _size=-1):
        self._read_count += 1
        if self._read_count == 1:
            return b"partial"
        raise TimeoutError("stream timed out")


def test_request_with_retries_returns_success_after_timeout(monkeypatch, caplog):
    """A transient timeout should be retried and then return the response."""
    calls = []

    def fake_get(url, timeout, stream):
        calls.append((url, timeout, stream))
        if len(calls) == 1:
            raise requests.ReadTimeout("first attempt timed out")
        return FakeResponse(content=b"ok")

    monkeypatch.setattr(cds_paper_bot.requests, "get", fake_get)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", lambda _seconds: None)
    caplog.set_level(logging.WARNING)

    response = cds_paper_bot.request_with_retries(
        "https://cds.cern.ch/rss",
        phase="RSS",
        experiment="CMS",
        feed_id="CMS_PAPER_FEED",
        retries=2,
        retry_delay=0,
    )

    assert response.content == b"ok"
    assert len(calls) == 2
    assert calls[0] == ("https://cds.cern.ch/rss", cds_paper_bot.REQUEST_TIMEOUT, False)
    assert "feed_id=CMS_PAPER_FEED" in caplog.text
    assert "attempt=1/2" in caplog.text


def test_request_with_retries_returns_none_after_final_timeout(monkeypatch, caplog):
    """Exhausted transient failures should return None instead of raising."""
    calls = []

    def fake_get(url, timeout, stream):
        calls.append((url, timeout, stream))
        raise requests.ReadTimeout("still timing out")

    monkeypatch.setattr(cds_paper_bot.requests, "get", fake_get)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", lambda _seconds: None)
    caplog.set_level(logging.WARNING)

    response = cds_paper_bot.request_with_retries(
        "https://cds.cern.ch/files/Figure_001.png",
        phase="media check",
        experiment="CMS",
        identifier="CMS-PAS-EXO-25-001",
        retries=2,
        retry_delay=0,
    )

    assert response is None
    assert len(calls) == 2
    assert "identifier=CMS-PAS-EXO-25-001" in caplog.text
    assert "Giving up request" in caplog.text


def test_media_url_exists_skips_timeout(monkeypatch, caplog):
    """Media checks should skip failed media rather than raising."""

    def fake_get(url, timeout, stream):
        raise requests.ReadTimeout(f"{url} timed out")

    monkeypatch.setattr(cds_paper_bot.requests, "get", fake_get)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", lambda _seconds: None)
    caplog.set_level(logging.WARNING)

    assert not cds_paper_bot.media_url_exists(
        "https://cds.cern.ch/files/Figure_001.png",
        experiment="CMS",
        identifier="CMS-PAS-EXO-25-001",
        retries=1,
        retry_delay=0,
    )
    assert "Skipping media after failed check" in caplog.text


def test_download_media_url_removes_partial_file(monkeypatch, tmp_path, caplog):
    """Streaming failures should not leave partial media files behind."""

    def fake_get(url, timeout, stream):
        assert stream
        return FakeResponse(status_code=200, raw=ChunkThenFailRaw())

    monkeypatch.setattr(cds_paper_bot.requests, "get", fake_get)
    caplog.set_level(logging.WARNING)
    out_path = tmp_path / "Figure_001.png"

    assert not cds_paper_bot.download_media_url(
        "https://cds.cern.ch/files/Figure_001.png",
        str(out_path),
        experiment="CMS",
        identifier="CMS-PAS-EXO-25-001",
        retries=1,
        retry_delay=0,
    )
    assert not out_path.exists()
    assert "Failed while streaming media download" in caplog.text


def test_read_feed_allows_slow_rss_without_extending_media_timeouts(monkeypatch):
    """CDS feeds can take longer than the normal ten-second request budget."""
    calls = []

    def fake_get(url, timeout, stream):
        calls.append(timeout)
        if timeout < 30:
            raise requests.ReadTimeout("RSS generation took thirty seconds")
        return FakeResponse(
            content=(
                b'<rss version="2.0"><channel><title>CMS Papers</title>'
                b"<item><title>A measurement</title></item></channel></rss>"
            )
        )

    monkeypatch.setattr(cds_paper_bot.requests, "get", fake_get)
    feed = cds_paper_bot.read_feed("https://cds.cern.ch/rss", feed_id="CMS_PAPER_FEED")

    assert [entry.title for entry in feed.entries] == ["A measurement"]
    assert calls == [cds_paper_bot.FEED_TIMEOUT]
    assert cds_paper_bot.REQUEST_TIMEOUT == 10


def test_read_feed_still_fails_after_exhausting_timeouts(monkeypatch, caplog):
    """A persistent CDS outage remains a failed feed rather than an empty success."""
    calls = []

    def fake_get(url, timeout, stream):
        calls.append(timeout)
        raise requests.ReadTimeout("CDS unavailable")

    monkeypatch.setattr(cds_paper_bot.requests, "get", fake_get)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", lambda _seconds: None)
    caplog.set_level(logging.WARNING)

    assert cds_paper_bot.read_feed("https://cds.cern.ch/rss") is None
    assert calls == [cds_paper_bot.FEED_TIMEOUT] * cds_paper_bot.REQUEST_RETRIES
    assert "Giving up request" in caplog.text
