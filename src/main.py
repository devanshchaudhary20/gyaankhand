"""Daily orchestrator with two stages so CI can commit-and-push between them.

Subcommands:
  render          Pick a verse, render the image, write to posts/ and state/_pending.json.
                  This is what CI runs first; CI then commits posts/ and state/_pending.json.
  publish         Read state/_pending.json, call Instagram Graph API, record to state/posted.json.
                  CI runs this after the commit so the image URL is live.
  publish-yt      Upload the most-recently-rendered video to YouTube Shorts.
                  Reads the last entry from state/posted.json for the file path, then updates
                  that entry with the YouTube video ID. Skips gracefully if YT creds are absent.
  all             Render + publish (Instagram) + publish-yt in one go (local testing).

Flags:
  --dry-run       (render mode) Skip writing the pending state file. Just renders the image.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config, image_renderer, instagram_poster, verse_loader, video_renderer

PENDING_FILE = config.STATE_DIR / "_pending.json"


def build_yt_title(verse: dict) -> str:
    title = f"{verse['source']} | Daily Sanskrit Verse #Shorts"
    return title[:100]


def build_yt_description(verse: dict) -> str:
    parts = [
        verse["translation_en"],
        "",
        f"— {verse['source']}",
    ]
    if config.YT_CHANNEL_HANDLE:
        parts.extend(["", f"Subscribe to {config.YT_CHANNEL_HANDLE} for daily verses."])
    elif config.IG_HANDLE:
        parts.extend(["", f"Follow {config.IG_HANDLE} on Instagram for daily verses."])
    parts.extend(["", config.HASHTAGS, "", "#Shorts"])
    return "\n".join(parts)


def build_caption(verse: dict) -> str:
    parts = [
        verse["translation_en"],
        "",
        f"— {verse['source']}",
    ]
    if config.IG_HANDLE:
        parts.extend(["", f"Follow {config.IG_HANDLE} for daily verses."])
    parts.extend(["", config.HASHTAGS])
    return "\n".join(parts)


def render_step(dry_run: bool = False) -> dict:
    verse = verse_loader.pick_next_verse()
    base_image = verse_loader.pick_base_image()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    video_relpath = f"posts/{timestamp}-{verse['id']}.mp4"
    video_path = config.ROOT / video_relpath
    # Intermediate image (not committed to the repo)
    image_path = video_path.with_suffix(".jpg")

    print(f"[gyaankhand] verse:  {verse['id']} ({verse['source']})")
    print(f"[gyaankhand] base:   {base_image.name}")
    print(f"[gyaankhand] output: {video_path}")

    image_renderer.render_verse(
        base_image_path=base_image,
        devanagari_text=verse["text_devanagari"],
        iast_text=verse["text_iast"],
        translation_en=verse["translation_en"],
        output_path=image_path,
        handle=config.IG_HANDLE or None,
    )
    video_renderer.render_reel(image_path=image_path, output_path=video_path)
    image_path.unlink(missing_ok=True)  # only the video is committed

    info = {
        "verse_id": verse["id"],
        "video_relpath": video_relpath,
        "caption": build_caption(verse),
        "rendered_at": datetime.now(timezone.utc).isoformat(),
    }

    if not dry_run:
        PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PENDING_FILE.open("w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        print(f"[gyaankhand] pending state written to {PENDING_FILE}")
    return info


def publish_step(info: dict | None = None) -> str:
    if info is None:
        if not PENDING_FILE.exists():
            raise RuntimeError(
                f"No pending render found at {PENDING_FILE}. Run 'render' first."
            )
        with PENDING_FILE.open("r", encoding="utf-8") as f:
            info = json.load(f)

    config.assert_runtime_config()

    video_url = instagram_poster.public_media_url(info["video_relpath"])
    print(f"[gyaankhand] video url: {video_url}")

    media_id = instagram_poster.post(video_url=video_url, caption=info["caption"])
    print(f"[gyaankhand] published media id: {media_id}")

    verse_loader.record_post(
        verse_id=info["verse_id"],
        image_relpath=info["video_relpath"],
        ig_media_id=media_id,
    )

    if PENDING_FILE.exists():
        PENDING_FILE.unlink()
    return media_id


def publish_yt_step() -> str:
    """Upload the most-recently-rendered video to YouTube Shorts.

    Reads the last posted.json entry (written by publish_step) to find the
    local video file, reconstructs the caption from verses.json, uploads,
    then records the YouTube video ID back into posted.json.

    Returns the YouTube video ID, or "" if credentials are not configured.
    """
    if not (config.YT_CLIENT_ID and config.YT_CLIENT_SECRET and config.YT_REFRESH_TOKEN):
        print("[gyaankhand] YouTube credentials not set — skipping YouTube upload.")
        return ""

    from . import youtube_poster  # imported here so missing google deps don't break other cmds

    if not config.POSTED_FILE.exists():
        raise RuntimeError("No posted.json found. Run 'publish' first.")

    with config.POSTED_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    entries = state.get("posted", [])
    if not entries:
        raise RuntimeError("posted.json has no entries.")

    last = entries[-1]
    video_path = config.ROOT / last["image"]
    if not video_path.exists():
        raise RuntimeError(f"Video file not found: {video_path}")

    verse_id = last["verse_id"]
    verses = verse_loader.load_verses()
    verse = next((v for v in verses if v["id"] == verse_id), None)

    if verse:
        title = build_yt_title(verse)
        description = build_yt_description(verse)
    else:
        title = "Daily Sanskrit Verse #Shorts"
        description = f"Daily Sanskrit verse.\n\n{config.HASHTAGS}\n\n#Shorts"

    print(f"[gyaankhand] uploading to YouTube Shorts: {video_path.name}")
    video_id = youtube_poster.post(
        video_path=video_path,
        title=title,
        description=description,
    )
    print(f"[gyaankhand] YouTube video id: {video_id}")

    verse_loader.record_yt_video_id(video_id)
    return video_id


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gyaankhand daily verse poster.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render", help="Render only.")
    r.add_argument("--dry-run", action="store_true")

    sub.add_parser("publish", help="Publish previously-rendered post to Instagram.")
    sub.add_parser("publish-yt", help="Upload most-recently-rendered video to YouTube Shorts.")
    sub.add_parser("all", help="Render, publish to Instagram, and upload to YouTube Shorts.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.cmd == "render":
        render_step(dry_run=args.dry_run)
    elif args.cmd == "publish":
        publish_step()
    elif args.cmd == "publish-yt":
        publish_yt_step()
    elif args.cmd == "all":
        info = render_step(dry_run=False)
        publish_step(info)
        publish_yt_step()
    return 0


if __name__ == "__main__":
    sys.exit(main())
