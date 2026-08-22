from __future__ import annotations

from pathlib import Path

from paperbot.models import LifecycleStage, Publication
from paperbot.state import (
    DeliveryLedger,
    find_existing_bluesky_post,
    find_existing_mastodon_post,
)


def publication():
    return Publication(
        experiment="CMS",
        feed_id="CMS_PAS_FEED",
        identifier="CMS-PAS-HIG-26-001",
        title="A measurement",
        link="https://cds.cern.ch/record/1",
        lifecycle_stage=LifecycleStage.PRELIMINARY,
    )


def test_partial_delivery_and_stale_ledger_writers_are_merged(tmp_path):
    first = DeliveryLedger(tmp_path, "CMS")
    stale = DeliveryLedger(tmp_path, "CMS")
    item = publication()
    first.mark(item, "mastodon", post_id="1")
    stale.mark(item, "bluesky", post_id="at://post")
    reloaded = DeliveryLedger(tmp_path, "CMS")
    assert reloaded.delivered(item, "mastodon")
    assert reloaded.delivered(item, "bluesky")
    assert (
        reloaded.data["publications"][item.canonical_key]["canonical_link"] == item.link
    )


def test_legacy_feed_files_migrate_without_being_modified(tmp_path):
    legacy = tmp_path / "MASTODON_CMS_PAS_FEED.txt"
    legacy.write_text("CMS-PAS-HIG-26-001\n", encoding="utf-8")
    ledger = DeliveryLedger(tmp_path / "ledger", "CMS")
    assert ledger.migrate_legacy(tmp_path) == 1
    assert legacy.read_text(encoding="utf-8") == "CMS-PAS-HIG-26-001\n"
    assert ledger.delivered(publication(), "mastodon")


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


def test_crash_after_publish_is_recovered_from_public_accounts(monkeypatch):
    responses = iter(
        [
            FakeResponse({"id": "account"}),
            FakeResponse(
                [
                    {
                        "id": "42",
                        "url": "https://mastodon.social/@cmspapers/42",
                        "content": "CMS-PAS-HIG-26-001",
                    }
                ]
            ),
        ]
    )
    monkeypatch.setattr(
        "paperbot.state.requests.get", lambda *args, **kwargs: next(responses)
    )
    assert find_existing_mastodon_post(
        "@cmspapers@mastodon.social",
        publication().identifier,
    ) == ("42", "https://mastodon.social/@cmspapers/42")

    monkeypatch.setattr(
        "paperbot.state.requests.get",
        lambda *args, **kwargs: FakeResponse(
            {
                "feed": [
                    {
                        "post": {
                            "uri": "at://did/app.bsky.feed.post/abc",
                            "record": {"text": "CMS-PAS-HIG-26-001"},
                        }
                    }
                ]
            }
        ),
    )
    assert find_existing_bluesky_post(
        "cmspapers.bsky.social",
        publication().identifier,
    ) == (
        "at://did/app.bsky.feed.post/abc",
        "https://bsky.app/profile/cmspapers.bsky.social/post/abc",
    )


def test_recovery_does_not_conflate_lifecycle_posts_sharing_a_link(monkeypatch):
    shared_link = publication().link
    old_identifier = "CERN-EP-2026-001"
    new_identifier = "arXiv:2608.00001"
    responses = iter(
        [
            FakeResponse({"id": "account"}),
            FakeResponse(
                [
                    {
                        "id": "42",
                        "url": "https://mastodon.social/@cmspapers/42",
                        "content": f"{old_identifier} {shared_link}",
                    }
                ]
            ),
        ]
    )
    monkeypatch.setattr(
        "paperbot.state.requests.get", lambda *args, **kwargs: next(responses)
    )
    assert (
        find_existing_mastodon_post(
            "@cmspapers@mastodon.social",
            new_identifier,
        )
        is None
    )

    monkeypatch.setattr(
        "paperbot.state.requests.get",
        lambda *args, **kwargs: FakeResponse(
            {
                "feed": [
                    {
                        "post": {
                            "uri": "at://did/app.bsky.feed.post/old",
                            "record": {"text": f"{old_identifier} {shared_link}"},
                        }
                    }
                ]
            }
        ),
    )
    assert (
        find_existing_bluesky_post(
            "cmspapers.bsky.social",
            new_identifier,
        )
        is None
    )


def test_gitlab_serializes_publishers_and_refreshes_state_before_posting():
    root = Path(__file__).resolve().parents[1]
    pipeline = (root / ".gitlab-ci.yml").read_text(encoding="utf-8")
    script = (root / ".gitlab" / "script.sh").read_text(encoding="utf-8")
    update_script = (root / ".gitlab" / "update_repo.sh").read_text(encoding="utf-8")
    assert pipeline.count("resource_group: cds-paper-bot-repository-writer") == 2
    assert "if: '$BUILD_IMAGE == \"true\"'" in pipeline
    assert 'ci.variable="BUILD_IMAGE=true"' in update_script
    assert update_script.index(
        "git checkout -B master origin/master"
    ) < update_script.index("git merge upstream/master")
    assert script.index("git checkout -B master origin/master") < script.index(
        "python cds_paper_bot.py"
    )
    assert "BOT_EXIT_CODE=$?" in script
    assert script.index("git add delivery-ledger") < script.index(
        'exit "${BOT_EXIT_CODE}"'
    )
