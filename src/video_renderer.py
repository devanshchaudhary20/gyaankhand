"""Convert a rendered image to a short MP4 suitable for Instagram Reels.

Requires ffmpeg to be installed (available by default on Ubuntu CI runners).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import config


def render_reel(image_path: Path, output_path: Path, duration: int | None = None) -> Path:
    """Create a static-image MP4 Reel from *image_path*.

    Duration defaults to config.REEL_DURATION (seconds).
    Returns output_path.
    """
    if duration is None:
        duration = config.REEL_DURATION

    output_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            # Ensure even dimensions; scale already matches config but be explicit.
            "-vf", f"scale={config.IMG_WIDTH}:{config.IMG_HEIGHT}",
            "-r", "30",
            "-movflags", "+faststart",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    return output_path
