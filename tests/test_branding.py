from __future__ import annotations

import hashlib

import pytest
from PIL import Image, ImageDraw

from paperbot import branding
from paperbot.branding import get_experiment_brand, render_branded_cover
from paperbot.models import (
    CoverPolicy,
    ExperimentBrand,
    LifecycleStage,
    Publication,
)


def publication(experiment: str = "CMS", title: str = "A precise measurement"):
    return Publication(
        experiment=experiment,
        feed_id=f"{experiment}_PAPER_FEED",
        identifier=f"{experiment}-PAPER-2026-001",
        title=title,
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=LifecycleStage.PAPER,
    )


@pytest.mark.parametrize(
    ("experiment", "expected_hash"),
    [
        ("CMS", "32889265c22cf93dbfe58f606701d3e143e35b77fe3daa91ed8538fbd08bf2f6"),
        ("ATLAS", "5554b1aecbfc5365afceee96fd36fdcda0a62fdf3c2a4b7ca7a65abb4f47ca7a"),
        ("LHCb", "f3eb9ef41f878b6260dbf4c3141d43e820978596bb526558694a4084b5ba2a16"),
        ("ALICE", "242c0e0aa491a3e8bf357a45d63d7684caead2d3fad3334cde1322735e81f2fe"),
    ],
)
def test_official_logo_assets_are_available_and_preserve_aspect_ratio(
    experiment, expected_hash
):
    brand = get_experiment_brand(experiment)
    assert brand.logo_path and brand.logo_path.is_file()
    assert hashlib.sha256(brand.logo_path.read_bytes()).hexdigest() == expected_hash
    with Image.open(brand.logo_path) as source:
        source_ratio = source.width / source.height
    rendered = branding._load_logo(brand, (310, 260))
    assert rendered is not None
    assert rendered.width <= 310 and rendered.height <= 260
    assert rendered.width / rendered.height == pytest.approx(source_ratio, rel=0.01)


@pytest.mark.parametrize("experiment", ["CMS", "LHCb", "ALICE", "OTHER"])
def test_card_golden_render_has_expected_copy_and_geometry(
    tmp_path, monkeypatch, experiment
):
    title = "A long but exact publication title " * 8
    captured_text = []
    original_text = ImageDraw.ImageDraw.text

    def capture(draw, xy, text, *args, **kwargs):
        captured_text.append(str(text))
        return original_text(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    item = publication(experiment, title.strip())
    path = render_branded_cover(item, tmp_path / f"{experiment}.png")
    with Image.open(path) as card:
        assert card.size == (1280, 720)
        assert card.mode == "RGB"
        assert card.getpixel((0, 300)) != (255, 255, 255)
    assert item.identifier in captured_text
    assert any(
        text
        in {
            "New preliminary result",
            "Paper coming soon to arXiv",
            "New paper on arXiv",
            "New paper",
        }
        for text in captured_text
    )
    assert " ".join(text for text in captured_text if text in item.title) == item.title
    assert not any("figures from CDS" in text.casefold() for text in captured_text)
    assert not any("figure" in text.casefold() for text in captured_text)


def test_unknown_experiment_uses_logo_free_card(tmp_path):
    brand = get_experiment_brand("FCC")
    assert brand.logo_path is None
    assert render_branded_cover(publication("FCC"), tmp_path / "fcc.png").is_file()


def test_missing_or_corrupt_logo_falls_back_to_text_card(tmp_path, monkeypatch):
    corrupt = tmp_path / "broken.png"
    corrupt.write_text("not an image", encoding="utf-8")
    monkeypatch.setitem(
        branding.EXPERIMENT_BRANDS,
        "CMS",
        ExperimentBrand(
            key="CMS",
            display_name="CMS",
            logo_path=corrupt,
            cover_policy=CoverPolicy.BRANDED_CARD,
        ),
    )
    output = render_branded_cover(publication(), tmp_path / "fallback.png")
    with Image.open(output) as card:
        assert card.size == (1280, 720)


@pytest.mark.parametrize(
    ("experiment", "title"),
    [
        (
            "CMS",
            (
                "Search for the rare Higgs boson decay H → Zγ in proton-proton "
                "collisions at √(s) = 13 and 13.6 TeV"
            ),
        ),
        (
            "LHCb",
            (
                "Stringent limits on CPT- and Lorentz-invariance violation from "
                "B⁰_s meson decays"
            ),
        ),
        ("LHCb", "Strong constraints on the K⁰_s → μ⁺ μ⁻ branching fraction"),
        ("CMS", "Measurement of γγ → τ⁺τ⁻ and J/ψ, Υ, χ, Λ, η, π and t̅ production"),
    ],
)
def test_cover_fonts_render_physics_symbols(tmp_path, monkeypatch, experiment, title):
    original_text = ImageDraw.ImageDraw.text
    rendered_symbols = set()

    def check_glyphs(draw, xy, text, *args, **kwargs):
        font = kwargs["font"]
        missing_glyph = font.getmask("\uffff")
        missing_signature = (missing_glyph.size, bytes(missing_glyph))
        for character in text:
            if ord(character) < 128:
                continue
            glyph = font.getmask(character)
            assert (glyph.size, bytes(glyph)) != missing_signature, repr(character)
            assert glyph.getbbox() is not None, repr(character)
            rendered_symbols.add(character)
        return original_text(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", check_glyphs)
    render_branded_cover(publication(experiment, title), tmp_path / "cover.png")
    assert rendered_symbols == {
        character for character in title if ord(character) > 127
    }


def test_missing_cover_fonts_fail_instead_of_rendering_boxes(tmp_path):
    with pytest.raises(OSError, match="Install fonts-dejavu-core"):
        branding._font((tmp_path / "missing.ttf",), 30)
