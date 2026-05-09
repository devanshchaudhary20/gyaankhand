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
VERSES_FILE = DATA_DIR / "verses.json"
FONTS_DIR = ROOT / "fonts"
STATE_DIR = ROOT / "state"
POSTED_FILE = STATE_DIR / "posted.json"
POSTS_DIR = ROOT / "posts"


# --- Fonts ---------------------------------------------------------------
FONT_DEVANAGARI = FONTS_DIR / "NotoSansDevanagari-Bold.ttf"
FONT_IAST = FONTS_DIR / "CrimsonText-Italic.ttf"
FONT_HANDLE = FONTS_DIR / "NotoSans-Regular.ttf"


# --- Image render settings ----------------------------------------------
IMG_WIDTH = 1080
IMG_HEIGHT = 1350
OVERLAY_OPACITY = 140  # 0-255; darker = more readable text
DEVANAGARI_FONT_SIZE = 56
IAST_FONT_SIZE = 36
HANDLE_FONT_SIZE = 28
TEXT_COLOR = (245, 240, 230)  # warm off-white
HANDLE_COLOR = (220, 215, 205)
SIDE_PADDING = 80  # pixels from left/right edges
LINE_SPACING_DEVANAGARI = 14
LINE_SPACING_IAST = 8
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
