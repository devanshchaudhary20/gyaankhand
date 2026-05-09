"""Picks the next verse and base image to use, with usage tracking."""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

from . import config


def _load_verses() -> list[dict]:
    with config.VERSES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_state() -> dict:
    if not config.POSTED_FILE.exists():
        return {"posted": []}
    with config.POSTED_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(state: dict) -> None:
    config.POSTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with config.POSTED_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def pick_next_verse() -> dict:
    """Pick a verse, preferring ones never posted; if all posted, pick the
    least-recently-used so the cycle continues fairly."""
    verses = _load_verses()
    if not verses:
        raise RuntimeError("verses.json is empty.")

    state = _load_state()
    posted = state.get("posted", [])
    used_ids = {p["verse_id"] for p in posted}
    last_used: dict[str, str] = {}
    for entry in posted:
        last_used[entry["verse_id"]] = entry.get("posted_at", "")

    unused = [v for v in verses if v["id"] not in used_ids]
    if unused:
        return random.choice(unused)

    # All have been posted at least once; pick the least-recently-used.
    verses_by_recency = sorted(verses, key=lambda v: last_used.get(v["id"], ""))
    return verses_by_recency[0]


def pick_base_image() -> Path:
    """Pick a random base image from data/base_images/."""
    candidates = [
        p
        for p in config.BASE_IMAGES_DIR.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        and not p.name.startswith("_")  # skip internal/test files
    ]
    if not candidates:
        raise RuntimeError(
            f"No base images found in {config.BASE_IMAGES_DIR}. "
            "Drop at least one .jpg/.png in there."
        )
    return random.choice(candidates)


def record_post(verse_id: str, image_relpath: str, ig_media_id: str) -> None:
    state = _load_state()
    state.setdefault("posted", []).append(
        {
            "verse_id": verse_id,
            "image": image_relpath,
            "ig_media_id": ig_media_id,
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save_state(state)
