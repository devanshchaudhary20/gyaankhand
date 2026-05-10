"""Centralized configuration. Loads from environment / .env file."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional in CI where env is set directly.
    pass


# --- Paths ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BASE_IMAGES_DIR = DATA_DIR / "base_images"
AUDIO_DIR = DATA_DIR / "audio"
VERSES_FILE = DATA_DIR / "verses.json"
FONTS_DIR = ROOT / "fonts"
STATE_DIR = ROOT / "state"
POSTED_FILE = STATE_DIR / "posted.json"
POSTS_DIR = ROOT / "posts"


# --- Fonts ---------------------------------------------------------------
FONT_DEVANAGARI = FONTS_DIR / "NotoSansDevanagari-Bold.ttf"
FONT_IAST = FONTS_DIR / "CrimsonText-Italic.ttf"
FONT_HANDLE = FONTS_DIR / "NotoSans-Regular.ttf"


# --- Image / video render settings --------------------------------------
IMG_WIDTH = 1080
IMG_HEIGHT = 1920   # 9:16 for Reels
REEL_DURATION = 30   # seconds

# Text panel overlay (drawn only behind the text block, not the whole image)
OVERLAY_COLOR = (255, 187, 153)   # warm orange tint
OVERLAY_OPACITY = 100           # 0-255
TEXT_PANEL_PADDING = 50         # pixels around the text inside the panel
TEXT_PANEL_CORNER_RADIUS = 28

DEVANAGARI_FONT_SIZE = 56
IAST_FONT_SIZE = 34
ENGLISH_FONT_SIZE = 30
HANDLE_FONT_SIZE = 28
TEXT_COLOR = (245, 240, 230)        # warm off-white — Devanagari + IAST
ENGLISH_TEXT_COLOR = (255, 248, 220) # slightly warmer — translation
HANDLE_COLOR = (220, 215, 205)
SIDE_PADDING = 80  # pixels from left/right edges
LINE_SPACING_DEVANAGARI = 14
LINE_SPACING_IAST = 8
LINE_SPACING_ENGLISH = 10
GAP_BETWEEN_BLOCKS = 40


# --- Instagram API (Instagram Login flow) -------------------------------
# Uses graph.instagram.com (not graph.facebook.com) — no Facebook Page needed.
IG_LONG_LIVED_TOKEN = os.getenv("IG_LONG_LIVED_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_APP_ID = os.getenv("IG_APP_ID", "")          # Instagram-specific app id, only needed for token refresh
IG_APP_SECRET = os.getenv("IG_APP_SECRET", "")  # Instagram-specific app secret
IG_API_VERSION = os.getenv("IG_API_VERSION", "v22.0")
IG_API_HOST = "https://graph.instagram.com"


# --- GitHub repo (for hosting the rendered image) -----------------------
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
IG_HANDLE = os.getenv("IG_HANDLE", "")


# --- YouTube API (OAuth 2.0 with offline refresh token) -----------------
# Generate the refresh token once locally using scripts/youtube_auth_setup.py,
# then store it as a GitHub secret (YT_REFRESH_TOKEN).
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN", "")
YT_CHANNEL_HANDLE = os.getenv("YT_CHANNEL_HANDLE", "")  # e.g. @gyaankhand


# --- Caption template ----------------------------------------------------
HASHTAGS = (
    "#bhagavadgita #sanskrit #vedanta #hinduism #spirituality "
    "#sanatandharma #yoga #bhakti #upanishads #vedas #ashtavakra "
    "#shiva #krishna #wisdom #dailyverse"
)


def assert_runtime_config() -> None:
    """Fail fast if Instagram credentials are missing."""
    missing = [
        name
        for name, value in [
            ("IG_LONG_LIVED_TOKEN", IG_LONG_LIVED_TOKEN),
            ("IG_USER_ID", IG_USER_ID),
            ("GITHUB_REPO", GITHUB_REPO),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "See .env.example."
        )


def assert_yt_config() -> None:
    """Fail fast if YouTube credentials are missing."""
    missing = [
        name
        for name, value in [
            ("YT_CLIENT_ID", YT_CLIENT_ID),
            ("YT_CLIENT_SECRET", YT_CLIENT_SECRET),
            ("YT_REFRESH_TOKEN", YT_REFRESH_TOKEN),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required YouTube environment variables: {', '.join(missing)}. "
            "See .env.example."
        )
