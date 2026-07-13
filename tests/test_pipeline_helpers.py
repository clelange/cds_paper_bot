from __future__ import annotations

from pathlib import Path

import cds_paper_bot
from paperbot.models import LifecycleStage, Publication


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
