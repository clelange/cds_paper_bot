from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import cds_paper_bot
from paperbot.models import LifecycleStage, MediaSequence, Publication


def publication():
    return Publication(
        experiment="CMS",
        feed_id="CMS_PAS_FEED",
        identifier="CMS-PAS-HIG-26-001",
        title="A measurement",
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=LifecycleStage.PRELIMINARY,
    )


def test_media_urls_are_downloaded_once_with_stable_order(tmp_path, monkeypatch):
    calls = []

    def fake_download(url, output, **kwargs):
        calls.append(url)
        Path(output).write_bytes(url.encode("utf-8"))
        return True

    monkeypatch.setattr(cds_paper_bot, "download_media_url", fake_download)
    first = "https://cds.cern.ch/files/Figure_2.png"
    second = "https://cds.cern.ch/files/Figure_1.png"
    results = cds_paper_bot.download_media_candidates(
        [(first, "figure"), (first, "figure"), (second, "figure")],
        tmp_path,
        experiment="CMS",
        feed_id="CMS_PAS_FEED",
        identifier="CMS-PAS-HIG-26-001",
        workers=2,
    )
    assert calls.count(first) == 1
    assert calls.count(second) == 1
    assert [path.name for _, path in results] == ["Figure_2.png", "Figure_1.png"]


def test_maximum_figures_is_applied_after_natural_ordering(tmp_path, monkeypatch):
    figures = [
        tmp_path / "Figure_10.png",
        tmp_path / "Figure_2.png",
        tmp_path / "Figure_1.png",
    ]
    monkeypatch.setattr(
        cds_paper_bot,
        "download_media_candidates",
        lambda *args, **kwargs: [("figure", path) for path in figures],
    )
    prepared = cds_paper_bot._prepare_publication_media(
        publication(), {}, 2, tmp_path / "output"
    )
    assert [path.name for path in prepared.media_paths] == [
        "Figure_1.png",
        "Figure_2.png",
    ]


def test_bluesky_video_failure_falls_back_to_supplied_static_media(
    tmp_path, monkeypatch
):
    video = tmp_path / "animation.mp4"
    image = tmp_path / "cover.png"
    video.write_bytes(b"video")
    image.write_bytes(b"image")
    uploaded = []

    def upload_blob(data):
        uploaded.append(data)
        if data == b"video":
            raise RuntimeError("video service unavailable")
        return SimpleNamespace(blob="image-blob")

    client = SimpleNamespace(
        com=SimpleNamespace(
            atproto=SimpleNamespace(
                repo=SimpleNamespace(upload_blob=upload_blob),
            )
        )
    )
    monkeypatch.setattr(
        cds_paper_bot.atproto_models.AppBskyEmbedImages,
        "Image",
        lambda **kwargs: kwargs,
    )

    media = cds_paper_bot.bluesky_upload_media(
        client,
        [str(video), str(image)],
        "CMS-PAS-HIG-26-001",
        alt_text="Accessible description",
    )

    assert uploaded == [b"video", b"image"]
    assert media == [{"image": "image-blob", "alt": "Accessible description"}]


def test_mastodon_gif_failure_uses_static_media_before_posting(tmp_path, monkeypatch):
    class FeedEntry(dict):
        __getattr__ = dict.__getitem__

    class FakeLedger:
        marks = []

        def __init__(self, *args, **kwargs):
            pass

        def migrate_legacy(self, *args, **kwargs):
            return 0

        def delivered(self, *args, **kwargs):
            return False

        def mark(self, publication, platform, **details):
            self.marks.append((publication.identifier, platform, details))

    post = FeedEntry(
        dc_source="CMS-PAS-HIG-26-001",
        feed_id="CMS_PAS_FEED",
        published="2026-08-22T10:00:00Z",
        title="A measurement",
        link="https://cds.cern.ch/record/1",
    )
    gif_path = tmp_path / "animation.gif"
    cover_path = tmp_path / "cover.png"
    gif_path.write_bytes(b"gif")
    cover_path.write_bytes(b"cover")
    upload_modes = []
    posted = []

    def upload_media(client, paths, post_gif, alt_text=""):
        upload_modes.append((post_gif, paths, alt_text))
        if post_gif:
            raise RuntimeError("GIF rejected")
        return ["static-media-id"]

    def post_status(
        client,
        type_hashtag,
        title,
        identifier,
        link,
        conference_hashtags,
        physics_hashtags,
        image_ids,
        post_gif,
        handle,
        message_list=None,
    ):
        posted.append(
            {
                "image_ids": image_ids,
                "post_gif": post_gif,
                "message_list": message_list,
            }
        )
        return {"id": "42", "url": "https://mastodon.social/@cmspapers/42"}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cds_paper_bot.atexit, "register", lambda function: None)
    monkeypatch.setattr(
        cds_paper_bot,
        "load_config",
        lambda *args: {
            "FEED_DICT": {"CMS_PAS_FEED": "https://cds.cern.ch/rss"},
            "AUTH": {"MASTODON_BOT_HANDLE": "@cmspapers@mastodon.social"},
        },
    )
    monkeypatch.setattr(
        cds_paper_bot, "_load_feed_entries", lambda *args: ([post], False)
    )
    monkeypatch.setattr(cds_paper_bot, "DeliveryLedger", FakeLedger)
    monkeypatch.setattr(cds_paper_bot, "twitter_auth", lambda *args: None)
    monkeypatch.setattr(cds_paper_bot, "mastodon_auth", lambda *args: object())
    monkeypatch.setattr(cds_paper_bot, "bluesky_auth", lambda *args: None)
    monkeypatch.setattr(cds_paper_bot, "_adopt_remote_delivery", lambda *args: False)
    monkeypatch.setattr(
        cds_paper_bot,
        "_prepare_publication_media",
        lambda item, *args: item,
    )
    monkeypatch.setattr(
        cds_paper_bot,
        "prepare_media_sequence",
        lambda *args, **kwargs: MediaSequence(
            gif_path=gif_path,
            static_paths=(cover_path,),
            alt_text="Accessible description",
        ),
    )
    monkeypatch.setattr(cds_paper_bot, "mastodon_upload_images", upload_media)
    monkeypatch.setattr(cds_paper_bot, "toot", post_status)
    monkeypatch.setattr(
        cds_paper_bot.sys,
        "argv",
        ["cds_paper_bot.py", "--experiment", "CMS", "--max", "1"],
    )

    cds_paper_bot.main()

    assert [post_gif for post_gif, _, _ in upload_modes] == [True, False]
    assert posted[0]["image_ids"] == ["static-media-id"]
    assert posted[0]["post_gif"] is False
    assert FakeLedger.marks[0][:2] == ("CMS-PAS-HIG-26-001", "mastodon")
