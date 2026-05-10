"""Daily orchestrator with two stages so CI can commit-and-push between them.

Subcommands:
  render          Pick a verse, render the image, write to posts/ and state/_pending.json.
                  This is what CI runs first; CI then commits posts/ and state/_pending.json.
  publish         Read state/_pending.json, call Instagram Graph API, record to state/posted.json.
                  CI runs this after the commit so the image URL is live.
  all             Render + publish in one go (useful for local testing once the repo is set up).

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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gyaankhand daily verse poster.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render", help="Render only.")
    r.add_argument("--dry-run", action="store_true")

    sub.add_parser("publish", help="Publish previously-rendered post.")
    sub.add_parser("all", help="Render and publish in one go.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.cmd == "render":
        render_step(dry_run=args.dry_run)
    elif args.cmd == "publish":
        publish_step()
    elif args.cmd == "all":
        info = render_step(dry_run=False)
        publish_step(info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
