from __future__ import annotations

import pytest

from paperbot.models import LifecycleStage, Publication
from paperbot.rendering import BlueskyRenderer, MastodonRenderer, physics_hashtag


def publication(identifier, stage, title="Title"):
    return Publication(
        experiment="CMS",
        feed_id="CMS_FEED",
        identifier=identifier,
        title=title,
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=stage,
    )


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (
            publication("CMS-PAS-HIG-26-001", LifecycleStage.PRELIMINARY),
            "New CMS preliminary result: Title (CMS-PAS-HIG-26-001) "
            "https://cds.cern.ch/record/1 #CMSPAS #HiggsBoson",
        ),
        (
            publication("CERN-EP-2026-001", LifecycleStage.PRE_ARXIV),
            "CMS paper — coming soon to arXiv: Title (CERN-EP-2026-001) "
            "https://cds.cern.ch/record/1 #CMSpaper",
        ),
        (
            publication("arXiv:2607.00001", LifecycleStage.ARXIV),
            "New CMS paper on arXiv: Title (arXiv:2607.00001) "
            "https://cds.cern.ch/record/1 #CMSpaper",
        ),
    ],
)
def test_lifecycle_templates_snapshot(item, expected):
    assert MastodonRenderer().render(item).messages == (expected,)
    assert BlueskyRenderer().render(item).messages == (expected,)


def test_identifier_topic_is_reliable_and_limited_to_one():
    item = publication("CMS-PAS-TAU-26-001", LifecycleStage.PRELIMINARY)
    assert physics_hashtag(item) == "#TauLeptons"
    assert (
        physics_hashtag(publication("CERN-EP-2026-001", LifecycleStage.PRE_ARXIV)) == ""
    )


@pytest.mark.parametrize("renderer", [MastodonRenderer(), BlueskyRenderer()])
def test_long_exact_title_is_threaded_with_canonical_link_on_root(renderer):
    title = "Measurement of " + "very important observable " * 40
    item = publication("CMS-PAS-SMP-26-001", LifecycleStage.PRELIMINARY, title)
    rendered = renderer.render(item)
    assert len(rendered.messages) > 1
    assert all(len(message) <= renderer.maximum_length for message in rendered.messages)
    assert item.link in rendered.messages[0]
    reconstructed = " ".join(rendered.messages).replace("…", "")
    for word in item.title.split():
        assert word in reconstructed
