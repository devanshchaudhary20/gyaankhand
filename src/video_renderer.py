"""Convert a rendered image to a short MP4 suitable for Instagram Reels.

Requires ffmpeg to be installed (available by default on Ubuntu CI runners).
If audio files exist in data/audio/, one is picked at random and mixed in.
"""
from __future__ import annotations

import random
import subprocess
from pathlib import Path

from . import config


def _pick_audio() -> Path | None:
    """Return a random audio file from AUDIO_DIR, or None if the dir is empty."""
    if not config.AUDIO_DIR.exists():
        return None
    tracks = list(config.AUDIO_DIR.glob("*.mp3")) + list(config.AUDIO_DIR.glob("*.m4a"))
    return random.choice(tracks) if tracks else None


def render_reel(image_path: Path, output_path: Path, duration: int | None = None) -> Path:
    """Create an MP4 Reel from *image_path*, optionally with background audio.

    Duration defaults to config.REEL_DURATION (seconds).
    Returns output_path.
    """
    if duration is None:
        duration = config.REEL_DURATION

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio = _pick_audio()

    if audio:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",       "-i", str(image_path),
            "-stream_loop", "-1", "-i", str(audio),
            "-c:v", "libx264",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={config.IMG_WIDTH}:{config.IMG_HEIGHT}",
            "-r", "30",
            "-movflags", "+faststart",
            "-shortest",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={config.IMG_WIDTH}:{config.IMG_HEIGHT}",
            "-r", "30",
            "-movflags", "+faststart",
            str(output_path),
        ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
