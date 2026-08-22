from __future__ import annotations

from pathlib import Path

from PIL import Image

from paperbot.media import (
    create_gif,
    deduplicate_media,
    natural_sort_key,
    normalize_plot,
    order_media,
    media_alt_text,
    prepare_media_sequence,
    select_cover,
)
from paperbot.models import LifecycleStage, Publication


def publication(experiment="CMS", documents=()):
    return Publication(
        experiment=experiment,
        feed_id=f"{experiment}_FEED",
        identifier=f"{experiment}-PAPER-2026-001",
        title="A test publication",
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=LifecycleStage.PAPER,
        document_paths=tuple(documents),
    )


def test_natural_order_and_alternate_format_deduplication():
    names = [Path("Figure_10.pdf"), Path("Figure_2.pdf"), Path("Figure_1.pdf")]
    assert [path.name for path in sorted(names, key=natural_sort_key)] == [
        "Figure_1.pdf",
        "Figure_2.pdf",
        "Figure_10.pdf",
    ]
    deduplicated = deduplicate_media(["Figure_2.pdf", "Figure_2.png", "Figure_1.pdf"])
    assert [path.name for path in deduplicated] == ["Figure_2.png", "Figure_1.pdf"]
    assert [path.name for path in order_media(names)] == [
        "Figure_1.pdf",
        "Figure_2.pdf",
        "Figure_10.pdf",
    ]


def test_scientific_plot_normalization_adds_no_branding_or_crop(tmp_path):
    source = tmp_path / "plot.png"
    Image.new("RGB", (320, 180), (210, 20, 30)).save(source)
    output = normalize_plot(source, tmp_path / "normalized.png")
    assert output is not None
    with Image.open(output) as normalized:
        assert normalized.size == (320, 180)
        red, green, blue = normalized.convert("RGB").getpixel((1, 1))
        assert red > 190 and green < 40 and blue < 50


def test_animation_frame_timing_and_size_fallback(tmp_path):
    cover = tmp_path / "cover.png"
    plot_1 = tmp_path / "plot-1.png"
    plot_2 = tmp_path / "plot-2.png"
    Image.new("RGB", (320, 180), "white").save(cover)
    Image.new("RGB", (320, 180), "red").save(plot_1)
    Image.new("RGB", (320, 180), "blue").save(plot_2)
    gif, retained = create_gif(cover, [plot_1, plot_2], tmp_path / "animation.gif")
    assert gif and retained == (plot_1, plot_2)
    with Image.open(gif) as animation:
        durations = []
        for frame in range(animation.n_frames):
            animation.seek(frame)
            durations.append(animation.info["duration"])
        assert durations == [4000, 3000, 3000]
    too_small, retained = create_gif(
        cover, [plot_1, plot_2], tmp_path / "tiny.gif", maximum_size=10
    )
    assert too_small is None
    assert len(retained) == 1


def test_atlas_title_page_and_card_fallback(tmp_path):
    document = tmp_path / "paper.pdf"
    Image.new("RGB", (600, 900), "navy").save(document, "PDF")
    cover = select_cover(publication("ATLAS", [document]), tmp_path / "title")
    assert cover is not None
    with Image.open(cover) as image:
        assert image.size == (1280, 720)
        assert image.convert("RGB").getpixel((640, 360)) != (255, 255, 255)

    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_text("not a PDF", encoding="utf-8")
    fallback = select_cover(publication("ATLAS", [corrupt]), tmp_path / "fallback")
    assert fallback is not None
    with Image.open(fallback) as image:
        assert image.size == (1280, 720)


def test_shared_animation_is_converted_to_mp4_exactly_once(tmp_path, monkeypatch):
    from paperbot import media as media_module

    plot_1 = tmp_path / "Figure_1.png"
    plot_2 = tmp_path / "Figure_2.png"
    Image.new("RGB", (320, 180), "red").save(plot_1)
    Image.new("RGB", (320, 180), "blue").save(plot_2)
    item = Publication(
        experiment="CMS",
        feed_id="CMS_FEED",
        identifier="CMS-PAS-HIG-26-001",
        title="A test publication",
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=LifecycleStage.PRELIMINARY,
        media_paths=(plot_1, plot_2),
    )
    calls = []
    original = media_module.convert_gif_to_mp4

    def counted_conversion(gif_path, output_path):
        calls.append((gif_path, output_path))
        return original(gif_path, output_path)

    monkeypatch.setattr(media_module, "convert_gif_to_mp4", counted_conversion)
    sequence = prepare_media_sequence(item, tmp_path / "prepared")
    assert sequence.gif_path and sequence.mp4_path
    assert len(calls) == 1
    assert calls[0][0] == sequence.gif_path


def test_long_alt_text_retains_timing_count_and_source_location():
    item = Publication(
        experiment="CMS",
        feed_id="CMS_FEED",
        identifier="CMS-PAS-HIG-26-001",
        title="An exceptionally detailed measurement " * 40,
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=LifecycleStage.PRELIMINARY,
    )
    alt_text = media_alt_text(item, 12, cover_included=True, animated=True)
    assert len(alt_text) <= 500
    assert "12 figures" in alt_text
    assert "four seconds" in alt_text and "three seconds" in alt_text
    assert "linked record provides the original files" in alt_text
