"""Deterministic post wording and identifier-derived topics."""

from __future__ import annotations

import re

from .branding import lifecycle_label
from .models import LifecycleStage, Publication, RenderedPost

CMS_TOPIC_TAGS = {
    "TOP": "#TopQuark",
    "HIG": "#HiggsBoson",
    "B2G": "#NewPhysics",
    "EXO": "#NewPhysics",
    "SUS": "#Supersymmetry",
    "FTR": "#Upgrade",
    "SMP": "#StandardModel",
    "BPH": "#BPhysics",
    "JME": "#Jets",
    "BTV": "#FlavourTagging",
    "MUO": "#Muons",
    "TAU": "#TauLeptons",
    "EGM": "#Photons",
    "LUM": "#Luminosity",
    "PRF": "#ParticleFlow",
    "HIN": "#HeavyIons",
}


def lifecycle_hashtag(publication: Publication) -> str:
    experiment = publication.experiment
    if publication.lifecycle_stage is LifecycleStage.PRELIMINARY:
        return "#CMSPAS" if experiment.upper() == "CMS" else f"#{experiment}conf"
    return f"#{experiment}paper"


def physics_hashtag(publication: Publication) -> str:
    """Derive at most one topic from a CMS analysis identifier."""
    if publication.experiment.upper() != "CMS":
        return ""
    match = re.search(r"CMS(?:-PAS)?-([A-Z]{3})-\d{2}-\d{3}", publication.identifier)
    if not match:
        return ""
    return CMS_TOPIC_TAGS.get(match.group(1), "")


def render_messages(publication: Publication, maximum_length: int) -> RenderedPost:
    """Render full, unchanged titles into a root post and deterministic replies."""
    tags = " ".join(
        filter(None, [lifecycle_hashtag(publication), physics_hashtag(publication)])
    )
    suffix = " ".join(
        filter(None, [f"({publication.identifier})", publication.link, tags])
    )
    prefix = f"{lifecycle_label(publication)}: "
    full_message = f"{prefix}{publication.title} {suffix}".strip()
    if len(full_message) <= maximum_length:
        return RenderedPost(messages=(full_message,))

    root_suffix = " ".join(filter(None, [publication.link, tags]))
    root_budget = maximum_length - len(prefix) - len(root_suffix) - 2
    title_words = publication.title.split()
    root_words: list[str] = []
    while title_words:
        candidate = " ".join(root_words + [title_words[0]])
        if len(candidate) > root_budget:
            break
        root_words.append(title_words.pop(0))
    root_title = " ".join(root_words).strip()
    root = f"{prefix}{root_title}… {root_suffix}".strip()

    continuation_text = " ".join(title_words).strip()
    continuation_text = f"…{continuation_text} ({publication.identifier})"
    replies: list[str] = []
    while continuation_text:
        if len(continuation_text) <= maximum_length:
            replies.append(continuation_text)
            break
        cut = continuation_text[: maximum_length - 1].rfind(" ")
        if cut <= 0:
            cut = maximum_length - 1
        replies.append(continuation_text[:cut].rstrip() + "…")
        continuation_text = "…" + continuation_text[cut:].lstrip()
    return RenderedPost(messages=tuple([root, *replies]))


class MastodonRenderer:
    name = "mastodon"
    maximum_length = 500

    def render(self, publication: Publication) -> RenderedPost:
        return render_messages(publication, self.maximum_length)


class BlueskyRenderer:
    name = "bluesky"
    maximum_length = 300

    def render(self, publication: Publication) -> RenderedPost:
        return render_messages(publication, self.maximum_length)
