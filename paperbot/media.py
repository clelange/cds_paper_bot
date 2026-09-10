"""Deterministic media normalization and animation generation."""

from __future__ import annotations

import logging
import math
import re
import subprocess
from collections.abc import Iterable, Sequence
from pathlib import Path

from PIL import Image as PillowImage
from PIL import ImageOps
from wand.exceptions import WandException
from wand.image import Color
from wand.image import Image as WandImage

from .branding import get_experiment_brand, render_branded_cover
from .models import CoverPolicy, MediaSequence, Publication

LOGGER = logging.getLogger(__name__)

COVER_SIZE = (1280, 720)
MAX_PLOT_DIMENSION = 1000
MAX_PLOT_AREA = 1280 * 720
MAX_ANIMATION_SIZE = 5 * 1024 * 1024
COVER_DURATION_MS = 4000
# Match the original ImageMagick `convert -delay 200` (centiseconds).
PLOT_DURATION_MS = 2000
FORMAT_PRIORITY = {".png": 4, ".jpg": 3, ".jpeg": 3, ".webp": 2, ".pdf": 1}


def natural_sort_key(value: str | Path) -> tuple[object, ...]:
    """Sort numbered filenames in human order."""
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", str(value))
    )


def _media_identity(path: Path) -> str:
    stem = path.stem.rstrip("_").casefold()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


def deduplicate_media(paths: Iterable[str | Path]) -> list[Path]:
    """Preserve first-seen order while preferring a directly usable raster."""
    selected: dict[str, tuple[int, Path]] = {}
    order: list[str] = []
    for index, raw_path in enumerate(paths):
        path = Path(raw_path)
        identity = _media_identity(path)
        if identity not in selected:
            selected[identity] = (index, path)
            order.append(identity)
            continue
        original_index, existing = selected[identity]
        if FORMAT_PRIORITY.get(path.suffix.casefold(), 0) > FORMAT_PRIORITY.get(
            existing.suffix.casefold(), 0
        ):
            selected[identity] = (original_index, path)
    return [selected[identity][1] for identity in order]


def order_media(paths: Iterable[str | Path]) -> list[Path]:
    """Preserve source order, naturally sorting one numbered filename series."""
    selected = deduplicate_media(paths)
    numbered = [re.match(r"^(.*?)(\d+)", path.stem) for path in selected]
    if selected and all(numbered):
        prefixes = {match.group(1).casefold() for match in numbered if match}
        if len(prefixes) == 1:
            return sorted(selected, key=natural_sort_key)
    return selected


def _normalized_dimensions(width: int, height: int) -> tuple[int, int]:
    scale = min(
        1.0,
        MAX_PLOT_DIMENSION / max(width, height),
        math.sqrt(MAX_PLOT_AREA / max(width * height, 1)),
    )
    return max(1, int(width * scale)), max(1, int(height * scale))


def normalize_plot(path: Path, output_path: Path) -> Path | None:
    """Render the first page/frame to PNG without adding visual overlays."""
    try:
        with WandImage(filename=f"{path}[0]") as image:
            image.background_color = Color("white")
            image.alpha_channel = "remove"
            image.format = "png"
            image.compression_quality = 90
            target_width, target_height = _normalized_dimensions(*image.size)
            if image.size != (target_width, target_height):
                image.resize(target_width, target_height)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(filename=str(output_path))
        return output_path
    except (WandException, OSError, ValueError) as exception:
        LOGGER.warning("Skipping unreadable media %s: %s", path, exception)
        return None


def normalize_plots(paths: Sequence[Path], output_directory: Path) -> list[Path]:
    normalized: list[Path] = []
    for index, path in enumerate(order_media(paths), start=1):
        result = normalize_plot(path, output_directory / f"plot-{index:03d}.png")
        if result:
            normalized.append(result)
    return normalized


def render_title_page(document_path: Path, output_path: Path) -> Path | None:
    """Render an uncropped first page onto the standard white cover canvas."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f"{output_path.stem}-source.png")
    try:
        with WandImage(filename=f"{document_path}[0]", resolution=144) as page:
            page.background_color = Color("white")
            page.alpha_channel = "remove"
            page.format = "png"
            page.save(filename=str(temporary))
        with PillowImage.open(temporary) as source:
            rendered = ImageOps.contain(
                source.convert("RGB"), COVER_SIZE, PillowImage.Resampling.LANCZOS
            )
        canvas = PillowImage.new("RGB", COVER_SIZE, "white")
        left = (COVER_SIZE[0] - rendered.width) // 2
        top = (COVER_SIZE[1] - rendered.height) // 2
        canvas.paste(rendered, (left, top))
        canvas.save(output_path, format="PNG", optimize=True)
        return output_path
    except (WandException, OSError, ValueError) as exception:
        LOGGER.warning("Could not render title page %s: %s", document_path, exception)
        return None
    finally:
        temporary.unlink(missing_ok=True)


def select_cover(
    publication: Publication,
    output_directory: Path,
    cover_mode: str = "auto",
) -> Path | None:
    """Use ATLAS title pages when available, otherwise render the configured card."""
    if cover_mode == "none":
        return None
    output_path = output_directory / "cover.png"
    brand = get_experiment_brand(publication.experiment)
    if brand.cover_policy is CoverPolicy.TITLE_PAGE_THEN_CARD:
        documents = sorted(publication.document_paths, key=natural_sort_key)
        for document in documents:
            rendered = render_title_page(document, output_path)
            if rendered:
                return rendered
    return render_branded_cover(publication, output_path)


def _canvas_dimensions(paths: Sequence[Path]) -> tuple[int, int]:
    width, height = COVER_SIZE
    for path in paths:
        try:
            with PillowImage.open(path) as frame:
                width = max(width, frame.width)
                height = max(height, frame.height)
        except OSError:
            continue
    return width, height


def _canvas_frame(path: Path, size: tuple[int, int], scale: float) -> PillowImage.Image:
    target_size = (max(2, int(size[0] * scale)), max(2, int(size[1] * scale)))
    with PillowImage.open(path) as source:
        contained = ImageOps.contain(
            source.convert("RGB"), target_size, PillowImage.Resampling.LANCZOS
        )
    canvas = PillowImage.new("RGB", target_size, "white")
    left = (target_size[0] - contained.width) // 2
    top = (target_size[1] - contained.height) // 2
    canvas.paste(contained, (left, top))
    return canvas


def _save_gif(
    paths: Sequence[Path],
    output_path: Path,
    cover_included: bool,
    scale: float,
) -> None:
    canvas_size = _canvas_dimensions(paths)
    frames = [_canvas_frame(path, canvas_size, scale) for path in paths]
    palette = getattr(PillowImage, "Palette", None)
    adaptive = palette.ADAPTIVE if palette else PillowImage.ADAPTIVE
    indexed = [frame.convert("P", palette=adaptive, colors=128) for frame in frames]
    durations = [PLOT_DURATION_MS] * len(indexed)
    if cover_included and durations:
        durations[0] = COVER_DURATION_MS
    output_path.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        output_path,
        save_all=True,
        append_images=indexed[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    for frame in frames:
        frame.close()
    for frame in indexed:
        frame.close()


def create_gif(
    cover_path: Path | None,
    plot_paths: Sequence[Path],
    output_path: Path,
    maximum_size: int = MAX_ANIMATION_SIZE,
) -> tuple[Path | None, tuple[Path, ...]]:
    """Create a bounded animation, scaling before dropping trailing plots."""
    paths = ([cover_path] if cover_path else []) + list(plot_paths)
    if len(paths) < 2:
        return None, tuple(plot_paths)
    retained_plots = list(plot_paths)
    for scale in (1.0, 0.875, 0.75, 0.625):
        current = ([cover_path] if cover_path else []) + retained_plots
        _save_gif(current, output_path, cover_path is not None, scale)
        if output_path.stat().st_size <= maximum_size:
            return output_path, tuple(retained_plots)
    while len(retained_plots) > 1:
        retained_plots.pop()
        current = ([cover_path] if cover_path else []) + retained_plots
        _save_gif(current, output_path, cover_path is not None, 0.625)
        if output_path.stat().st_size <= maximum_size:
            return output_path, tuple(retained_plots)
    if output_path.exists() and output_path.stat().st_size <= maximum_size:
        return output_path, tuple(retained_plots)
    output_path.unlink(missing_ok=True)
    return None, tuple(retained_plots)


def convert_gif_to_mp4(gif_path: Path, output_path: Path) -> Path | None:
    """Convert once using an argument-list subprocess and validated output."""
    command = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-i",
        str(gif_path),
        "-movflags",
        "+faststart",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-y",
        str(output_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exception:
        LOGGER.warning("GIF-to-MP4 conversion failed for %s: %s", gif_path, exception)
        output_path.unlink(missing_ok=True)
        return None
    if not output_path.is_file() or output_path.stat().st_size == 0:
        output_path.unlink(missing_ok=True)
        return None
    return output_path


def media_alt_text(
    publication: Publication,
    plot_count: int,
    *,
    cover_included: bool,
    animated: bool,
) -> str:
    """Describe deterministic media facts without inventing scientific content."""

    def bounded(render):
        text = render(publication.title)
        if len(text) <= 500:
            return text
        excess = len(text) - 497
        title_budget = max(24, len(publication.title) - excess)
        shortened = publication.title[:title_budget].rsplit(" ", 1)[0].rstrip() + "…"
        return render(shortened)[:500]

    if plot_count == 0:
        return bounded(
            lambda title: (
                f'Cover for "{title}" ({publication.identifier}). '
                "The linked record provides the publication and any original media files."
            )
        )
    plural = "figure" if plot_count == 1 else "figures"
    frame_order = "a cover followed by " if cover_included else ""
    if animated:
        timing = (
            " The cover is shown for about four seconds and each figure for about two "
            "seconds."
            if cover_included
            else " Each figure is shown for about two seconds."
        )
        return bounded(
            lambda title: (
                f'Animation for "{title}" ({publication.identifier}), containing '
                f"{frame_order}{plot_count} {plural} in the order published.{timing} The "
                "linked record provides the original files and any available captions."
            )
        )
    return bounded(
        lambda title: (
            f'Media for "{title}" ({publication.identifier}), containing '
            f"{frame_order}{plot_count} {plural} in the order published. The linked record "
            "provides the original files and any available captions."
        )
    )


def prepare_media_sequence(
    publication: Publication,
    output_directory: Path,
    *,
    create_animation: bool = True,
    cover_mode: str = "auto",
) -> MediaSequence:
    """Prepare shared media once for Mastodon, Bluesky, and optional Twitter."""
    output_directory.mkdir(parents=True, exist_ok=True)
    normalized_plots = normalize_plots(
        list(publication.media_paths), output_directory / "normalized"
    )
    cover_path = select_cover(publication, output_directory, cover_mode=cover_mode)
    if not normalized_plots:
        static = (cover_path,) if cover_path else ()
        return MediaSequence(
            cover_path=cover_path,
            static_paths=static,
            alt_text=media_alt_text(
                publication,
                0,
                cover_included=cover_path is not None,
                animated=False,
            ),
        )

    static_paths = tuple(([cover_path] if cover_path else []) + normalized_plots[:3])
    if not create_animation:
        return MediaSequence(
            cover_path=cover_path,
            plot_paths=tuple(normalized_plots),
            static_paths=static_paths[:4],
            alt_text=media_alt_text(
                publication,
                len(normalized_plots),
                cover_included=cover_path is not None,
                animated=False,
            ),
        )

    gif_path, retained = create_gif(
        cover_path,
        normalized_plots,
        output_directory / f"{publication.identifier.replace(':', '_')}.gif",
    )
    mp4_path = None
    if gif_path:
        mp4_path = convert_gif_to_mp4(gif_path, gif_path.with_suffix(".mp4"))
    return MediaSequence(
        cover_path=cover_path,
        plot_paths=retained,
        gif_path=gif_path,
        mp4_path=mp4_path,
        static_paths=static_paths[:4],
        alt_text=media_alt_text(
            publication,
            len(retained),
            cover_included=cover_path is not None,
            animated=gif_path is not None,
        ),
    )
