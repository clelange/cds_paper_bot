"""Regression tests for asynchronously processed Mastodon attachments."""

from types import SimpleNamespace

import pytest
import requests

import cds_paper_bot


@pytest.fixture
def clock(monkeypatch):
    state = SimpleNamespace(now=0.0, sleeps=[])

    def sleep(seconds):
        state.sleeps.append(seconds)
        state.now += seconds

    monkeypatch.setattr(cds_paper_bot.time, "monotonic", lambda: state.now)
    monkeypatch.setattr(cds_paper_bot.time, "sleep", sleep)
    return state


def test_gif_upload_waits_until_attachment_is_ready(clock):
    uploads = []
    polls = []
    responses = iter([{"id": 42, "url": None}, {"id": 42, "url": "https://media/42"}])

    def upload(**kwargs):
        uploads.append(kwargs)
        return {"id": 42, "url": None}

    def media(media_id):
        polls.append(media_id)
        return next(responses)

    ids = cds_paper_bot.mastodon_upload_images(
        SimpleNamespace(media_post=upload, media=media),
        ["animation.gif", "cover.png"],
        True,
        alt_text="Accessible description",
    )

    assert ids == [42]
    assert uploads == [
        {"media_file": "animation.gif", "description": "Accessible description"}
    ]
    assert polls == [42, 42]
    assert clock.sleeps == [2, 2]


def test_ready_static_upload_does_not_poll(clock):
    client = SimpleNamespace(
        media_post=lambda **kwargs: {"id": 7, "url": "https://media/7"},
    )
    assert cds_paper_bot.mastodon_upload_images(client, ["cover.png"], False) == [7]
    assert clock.sleeps == []


def test_empty_http_206_from_pinned_sdk_is_pending(clock, monkeypatch):
    responses = []
    for status, body in (
        (206, b""),
        (200, b'{"id": "42", "url": "https://media/42"}'),
    ):
        response = requests.Response()
        response.status_code = status
        response._content = body
        responses.append(response)
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url))
        return responses.pop(0)

    session = requests.Session()
    monkeypatch.setattr(session, "request", request)
    client = cds_paper_bot.mastodon.Mastodon(
        access_token="test-token",
        api_base_url="https://mastodon.example",
        mastodon_version="4.0.0",
        session=session,
    )

    assert cds_paper_bot._wait_for_mastodon_media(client, {"id": 42, "url": None}) == 42
    assert calls == [("GET", "https://mastodon.example/api/v1/media/42")] * 2
    assert clock.sleeps == [2, 2]


@pytest.mark.parametrize(
    "exception",
    [
        cds_paper_bot.mastodon.MastodonNetworkError("read timed out"),
        cds_paper_bot.mastodon.MastodonServiceUnavailableError("HTTP 503"),
    ],
)
def test_transient_polling_failure_reuses_attachment(clock, exception):
    polls = []

    def media(media_id):
        polls.append(media_id)
        if len(polls) == 1:
            raise exception
        return {"id": media_id, "url": "https://media/42"}

    client = SimpleNamespace(media=media)
    assert cds_paper_bot._wait_for_mastodon_media(client, {"id": 42, "url": None}) == 42
    assert polls == [42, 42]
    assert clock.sleeps == [2, 2]


@pytest.mark.parametrize(
    "exception",
    [
        cds_paper_bot.mastodon.MastodonUnauthorizedError("invalid token"),
        cds_paper_bot.mastodon.MastodonAPIError("media processing failed", 422),
        cds_paper_bot.mastodon.MastodonAPIError(
            "Could not parse response as JSON, response code was 200, bad json content was b''.",
        ),
    ],
)
def test_permanent_polling_error_is_propagated(clock, exception):
    def media(media_id):
        raise exception

    with pytest.raises(type(exception)) as raised:
        cds_paper_bot._wait_for_mastodon_media(
            SimpleNamespace(media=media),
            {"id": 42, "url": None},
        )
    assert raised.value is exception
    assert clock.sleeps == [2]


def test_processing_timeout_never_returns_unready_attachment(clock):
    polls = []

    def media(media_id):
        polls.append(media_id)
        return {"id": media_id, "url": None}

    with pytest.raises(
        cds_paper_bot.mastodon.MastodonError, match="processing timed out after 5s"
    ):
        cds_paper_bot._wait_for_mastodon_media(
            SimpleNamespace(media=media),
            {"id": 42, "url": None},
            timeout=5,
            poll_interval=2,
        )
    assert polls == [42, 42]
    assert clock.sleeps == [2, 2, 1]
