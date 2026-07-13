"""Offline experiment branding and deterministic cover-card rendering."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import CoverPolicy, ExperimentBrand, LifecycleStage, Publication

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_ROOT = PROJECT_ROOT / "img" / "logos"

EXPERIMENT_BRANDS: dict[str, ExperimentBrand] = {
    "CMS": ExperimentBrand(
        key="CMS",
        display_name="CMS",
        logo_path=LOGO_ROOT / "CMS.png",
        cover_policy=CoverPolicy.BRANDED_CARD,
        accent_color="#D71920",
    ),
    "ATLAS": ExperimentBrand(
        key="ATLAS",
        display_name="ATLAS",
        logo_path=LOGO_ROOT / "ATLAS.png",
        cover_policy=CoverPolicy.TITLE_PAGE_THEN_CARD,
        accent_color="#0B80C3",
    ),
    "LHCB": ExperimentBrand(
        key="LHCB",
        display_name="LHCb",
        logo_path=LOGO_ROOT / "LHCb.png",
        cover_policy=CoverPolicy.BRANDED_CARD,
        accent_color="#0054A6",
    ),
    "ALICE": ExperimentBrand(
        key="ALICE",
        display_name="ALICE",
        logo_path=LOGO_ROOT / "ALICE.png",
        cover_policy=CoverPolicy.BRANDED_CARD,
        accent_color="#E30613",
    ),
}

DEFAULT_BRAND = ExperimentBrand(
    key="OTHER",
    display_name="",
    logo_path=None,
    cover_policy=CoverPolicy.BRANDED_CARD,
)

FONT_REGULAR_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
)
FONT_BOLD_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
)


def get_experiment_brand(experiment: str) -> ExperimentBrand:
    """Return a known brand, or a safe logo-free fallback."""
    key = experiment.upper()
    brand = EXPERIMENT_BRANDS.get(key)
    if brand:
        return brand
    return ExperimentBrand(
        key=key,
        display_name=experiment,
        logo_path=None,
        cover_policy=CoverPolicy.BRANDED_CARD,
    )


def lifecycle_label(publication: Publication) -> str:
    """Return explicit, deterministic lifecycle wording."""
    display_name = get_experiment_brand(publication.experiment).display_name
    if publication.lifecycle_stage is LifecycleStage.PRELIMINARY:
        return f"New {display_name} preliminary result"
    if publication.lifecycle_stage is LifecycleStage.PRE_ARXIV:
        return f"{display_name} paper — coming soon to arXiv"
    if publication.lifecycle_stage is LifecycleStage.ARXIV:
        return f"New {display_name} paper on arXiv"
    return f"New {display_name} paper"


def cover_lifecycle_label(publication: Publication) -> str:
    """Return the compact lifecycle wording used beside an experiment logo."""
    if publication.lifecycle_stage is LifecycleStage.PRELIMINARY:
        return "New preliminary result"
    if publication.lifecycle_stage is LifecycleStage.PRE_ARXIV:
        return "Paper coming soon to arXiv"
    if publication.lifecycle_stage is LifecycleStage.ARXIV:
        return "New paper on arXiv"
    return "New paper"


def _font(candidates: tuple[Path, ...], size: int) -> ImageFont.ImageFont:
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    maximum_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textlength(candidate, font=font) <= maximum_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    maximum_width: int,
    maximum_height: int,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    for size in range(52, 21, -2):
        font = _font(FONT_BOLD_CANDIDATES, size)
        lines = _wrap_text(draw, title, font, maximum_width)
        line_height = int(size * 1.22)
        if len(lines) * line_height <= maximum_height:
            return font, lines, line_height
    font = _font(FONT_BOLD_CANDIDATES, 22)
    lines = _wrap_text(draw, title, font, maximum_width)
    return font, lines, 27


def _load_logo(
    brand: ExperimentBrand, maximum_size: tuple[int, int]
) -> Image.Image | None:
    if not brand.logo_path or not brand.logo_path.is_file():
        return None
    try:
        with Image.open(brand.logo_path) as source:
            logo = source.convert("RGBA")
        logo.thumbnail(maximum_size, Image.Resampling.LANCZOS)
        return logo
    except (OSError, ValueError):
        return None


def render_branded_cover(
    publication: Publication,
    output_path: Path,
    size: tuple[int, int] = (1280, 720),
) -> Path:
    """Render a readable, logo-aware cover without external network access."""
    width, height = size
    brand = get_experiment_brand(publication.experiment)
    canvas = Image.new("RGB", size, "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    accent = brand.accent_color

    draw.rectangle((0, 0, 20, height), fill=accent)
    draw.rectangle((20, 0, width, 12), fill=accent)

    logo = _load_logo(brand, (310, 260))
    text_left = 96
    if logo is not None:
        logo_left = 58 + max(0, (310 - logo.width) // 2)
        logo_top = 92 + max(0, (260 - logo.height) // 2)
        canvas.paste(logo, (logo_left, logo_top), logo)
        text_left = 420

    text_width = width - text_left - 76
    label_font = _font(FONT_BOLD_CANDIDATES, 30)
    draw.text(
        (text_left, 82),
        cover_lifecycle_label(publication),
        font=label_font,
        fill=accent,
    )

    title_font, title_lines, line_height = _fit_title(
        draw,
        publication.title,
        maximum_width=text_width,
        maximum_height=410,
    )
    title_top = 150
    for line in title_lines:
        draw.text((text_left, title_top), line, font=title_font, fill="#1C2731")
        title_top += line_height

    identifier_font = _font(FONT_REGULAR_CANDIDATES, 30)
    draw.text(
        (text_left, height - 82),
        publication.identifier,
        font=identifier_font,
        fill="#4B5965",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)
    return output_path
