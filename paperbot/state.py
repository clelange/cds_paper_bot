"""Durable delivery ledger and remote duplicate recovery."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

import requests

from .models import DeliveryRecord, Publication

SCHEMA_VERSION = 1


class DeliveryLedger:
    """One atomic JSON ledger per experiment."""

    def __init__(self, root: Path, experiment: str):
        self.root = root
        self.experiment = experiment.upper()
        self.path = root / f"{self.experiment}.json"
        self.data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "experiment": self.experiment,
            "publications": {},
        }
        self.load()

    def load(self) -> None:
        if not self.path.is_file():
            return
        with self.path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
        if loaded.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported delivery ledger schema: {self.path}")
        self.data = loaded

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            with self.path.open(encoding="utf-8") as handle:
                on_disk = json.load(handle)
            disk_publications = on_disk.get("publications", {})
            for key, disk_entry in disk_publications.items():
                if key not in self.data["publications"]:
                    self.data["publications"][key] = disk_entry
                    continue
                memory_entry = self.data["publications"][key]
                merged_platforms = dict(disk_entry.get("platforms", {}))
                merged_platforms.update(memory_entry.get("platforms", {}))
                memory_entry["platforms"] = merged_platforms
        temporary = self.path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, self.path)

    def _publication_entry(self, publication: Publication) -> dict[str, Any]:
        publications = self.data.setdefault("publications", {})
        entry = publications.setdefault(
            publication.canonical_key,
            {
                "identifier": publication.identifier,
                "feed_id": publication.feed_id,
                "lifecycle_stage": publication.lifecycle_stage.value,
                "title_fingerprint": publication.title_fingerprint,
                "canonical_link": publication.link,
                "platforms": {},
            },
        )
        return entry

    def get(self, publication: Publication, platform: str) -> DeliveryRecord | None:
        entry = self.data.get("publications", {}).get(publication.canonical_key, {})
        delivery = entry.get("platforms", {}).get(platform)
        if not delivery:
            return None
        return DeliveryRecord(**delivery)

    def delivered(self, publication: Publication, platform: str) -> bool:
        record = self.get(publication, platform)
        return bool(record and record.status in {"posted", "adopted", "migrated"})

    def mark(
        self,
        publication: Publication,
        platform: str,
        *,
        post_id: str = "",
        post_url: str = "",
        content_hash: str = "",
        adopted: bool = False,
        status: str | None = None,
    ) -> None:
        entry = self._publication_entry(publication)
        delivery = DeliveryRecord(
            status=status or ("adopted" if adopted else "posted"),
            post_id=post_id,
            post_url=post_url,
            posted_at=datetime.now(timezone.utc).isoformat(),
            content_hash=content_hash,
            adopted=adopted,
        )
        entry.setdefault("platforms", {})[platform] = delivery.__dict__
        self.save()

    def migrate_legacy(self, repository_root: Path) -> int:
        """Import old per-platform identifier files without modifying them."""
        migrated = 0
        for platform in ("MASTODON", "BLUESKY", "TWITTER"):
            pattern = f"{platform}_{self.experiment}_*_FEED.txt"
            for legacy_path in repository_root.glob(pattern):
                feed_id = legacy_path.stem[len(platform) + 1 :]
                for identifier in legacy_path.read_text(encoding="utf-8").splitlines():
                    identifier = identifier.strip()
                    if not identifier:
                        continue
                    key_source = "|".join(
                        [
                            self.experiment,
                            feed_id,
                            _stage_for_identifier(identifier),
                            identifier,
                        ]
                    )
                    digest = hashlib.sha256(key_source.encode("utf-8")).hexdigest()[:24]
                    key = f"{self.experiment}:{digest}"
                    entry = self.data.setdefault("publications", {}).setdefault(
                        key,
                        {
                            "identifier": identifier,
                            "feed_id": feed_id,
                            "lifecycle_stage": _stage_for_identifier(identifier),
                            "title_fingerprint": "",
                            "canonical_link": "",
                            "platforms": {},
                        },
                    )
                    if platform.lower() not in entry["platforms"]:
                        entry["platforms"][platform.lower()] = DeliveryRecord(
                            status="migrated"
                        ).__dict__
                        migrated += 1
        if migrated:
            self.save()
        return migrated


def _stage_for_identifier(identifier: str) -> str:
    if identifier.startswith("CERN-EP"):
        return "pre_arxiv"
    if identifier.lower().startswith("arxiv"):
        return "arxiv"
    if any(marker in identifier for marker in ("CMS-PAS", "ATLAS-CONF", "LHCb-CONF")):
        return "preliminary"
    return "paper"


def _plain_text(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def find_existing_mastodon_post(
    handle: str,
    identifier: str,
    link: str,
    expected_text_hash: str = "",
    timeout: float = 10,
) -> tuple[str, str] | None:
    """Find a recent public status after a crash-before-checkpoint scenario."""
    parts = [part for part in handle.split("@") if part]
    if len(parts) < 2:
        return None
    username, hostname = parts[-2], parts[-1]
    base = f"https://{hostname}"
    try:
        account_response = requests.get(
            f"{base}/api/v1/accounts/lookup",
            params={"acct": username},
            timeout=timeout,
        )
        account_response.raise_for_status()
        account_id = account_response.json()["id"]
        statuses_response = requests.get(
            f"{base}/api/v1/accounts/{account_id}/statuses",
            params={"limit": 40, "exclude_reblogs": "true"},
            timeout=timeout,
        )
        statuses_response.raise_for_status()
        for status in statuses_response.json():
            content = _plain_text(status.get("content", ""))
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if (
                identifier in content
                or (link and link in content)
                or (expected_text_hash and content_hash == expected_text_hash)
            ):
                return str(status.get("id", "")), str(status.get("url", ""))
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None
    return None


def find_existing_bluesky_post(
    handle: str,
    identifier: str,
    link: str,
    expected_text_hash: str = "",
    timeout: float = 10,
) -> tuple[str, str] | None:
    """Find a recent public Bluesky post without requiring account credentials."""
    try:
        response = requests.get(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed",
            params={"actor": handle, "limit": 50, "filter": "posts_no_replies"},
            timeout=timeout,
        )
        response.raise_for_status()
        for item in response.json().get("feed", []):
            post = item.get("post", {})
            text = post.get("record", {}).get("text", "")
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if (
                identifier in text
                or (link and link in text)
                or (expected_text_hash and content_hash == expected_text_hash)
            ):
                uri = str(post.get("uri", ""))
                post_id = uri.rsplit("/", 1)[-1]
                return uri, f"https://bsky.app/profile/{handle}/post/{post_id}"
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None
    return None
