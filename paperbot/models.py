"""Typed data exchanged between feed, media, state, and platform layers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, Sequence


class CoverPolicy(str, Enum):
    """How the first media frame is selected for an experiment."""

    BRANDED_CARD = "branded_card"
    TITLE_PAGE_THEN_CARD = "title_page_then_card"


class LifecycleStage(str, Enum):
    """Publication stage advertised by a post."""

    PRELIMINARY = "preliminary"
    PRE_ARXIV = "pre_arxiv"
    ARXIV = "arxiv"
    PAPER = "paper"


def lifecycle_stage_for(identifier: str) -> LifecycleStage:
    """Classify an identifier without relying on external metadata."""
    if any(marker in identifier for marker in ("CMS-PAS", "ATLAS-CONF", "LHCb-CONF")):
        return LifecycleStage.PRELIMINARY
    if identifier.startswith("CERN-EP"):
        return LifecycleStage.PRE_ARXIV
    if identifier.casefold().startswith("arxiv"):
        return LifecycleStage.ARXIV
    return LifecycleStage.PAPER


@dataclass(frozen=True)
class ExperimentBrand:
    """Offline branding configuration for one experiment."""

    key: str
    display_name: str
    logo_path: Path | None
    cover_policy: CoverPolicy
    accent_color: str = "#263746"


@dataclass(frozen=True)
class Publication:
    """Normalized publication data used by every output platform."""

    experiment: str
    feed_id: str
    identifier: str
    title: str
    link: str
    lifecycle_stage: LifecycleStage
    media_paths: tuple[Path, ...] = ()
    document_paths: tuple[Path, ...] = ()

    @property
    def title_fingerprint(self) -> str:
        """Return a stable fingerprint suitable for diagnostics and recovery."""
        normalized = re.sub(r"[^a-z0-9]+", " ", self.title.casefold()).strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]

    @property
    def canonical_key(self) -> str:
        """Keep lifecycle identifiers distinct while unifying platform delivery."""
        source = "|".join(
            [
                self.experiment.upper(),
                self.feed_id.upper(),
                self.lifecycle_stage.value,
                self.identifier,
            ]
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]
        return f"{self.experiment.upper()}:{digest}"


@dataclass(frozen=True)
class MediaSequence:
    """Prepared media shared by all platform adapters."""

    cover_path: Path | None = None
    plot_paths: tuple[Path, ...] = ()
    gif_path: Path | None = None
    mp4_path: Path | None = None
    static_paths: tuple[Path, ...] = ()
    alt_text: str = ""

    @property
    def has_animation(self) -> bool:
        return self.gif_path is not None


@dataclass(frozen=True)
class RenderedPost:
    """Platform-ready post text with a deterministic content hash."""

    messages: tuple[str, ...]

    @property
    def content_hash(self) -> str:
        payload = "\n---\n".join(self.messages)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class DeliveryRecord:
    """Persistent result of delivering one publication to one platform."""

    status: str
    post_id: str = ""
    post_url: str = ""
    posted_at: str = ""
    content_hash: str = ""
    adopted: bool = False


class PlatformRenderer(Protocol):
    """Minimal interface implemented by platform-specific renderers."""

    name: str
    maximum_length: int

    def render(self, publication: Publication) -> RenderedPost:
        """Render a normalized publication without changing scientific wording."""


@dataclass
class RunSummary:
    """Machine-readable outcome emitted by scheduled jobs."""

    experiment: str
    events: list[dict[str, str]] = field(default_factory=list)

    def add(self, event: str, **details: object) -> None:
        normalized = {"event": event}
        normalized.update({key: str(value) for key, value in details.items()})
        self.events.append(normalized)

    def required_failures(
        self, required_platforms: Sequence[str]
    ) -> list[dict[str, str]]:
        required = set(required_platforms)
        return [
            event
            for event in self.events
            if event.get("event") == "failed" and event.get("platform") in required
        ]
