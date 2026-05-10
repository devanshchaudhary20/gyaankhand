"""YouTube Shorts poster using YouTube Data API v3 with OAuth 2.0 refresh token.

Authentication:
  Uses a refresh token (offline access) stored as GitHub secrets. The token is
  exchanged for a short-lived access token at runtime — no interactive login needed.

  To generate the initial refresh token locally, run:
    python -m src.youtube_auth
  (see scripts/youtube_auth_setup.py for one-time setup instructions)

Upload flow:
  1. Exchange refresh token → access token (via google-auth)
  2. Call videos.insert with resumable upload (MediaFileUpload)
  3. Return the video ID

YouTube Shorts signals:
  - 9:16 aspect ratio (1080x1920) ✓ — already our output
  - Duration ≤ 60 seconds ✓ — our reels are 30 s
  - #Shorts in description ✓ — appended by build_yt_description()
"""
from __future__ import annotations

from pathlib import Path

import google.auth.transport.requests
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from . import config


def _credentials() -> google.oauth2.credentials.Credentials:
    creds = google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=config.YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YT_CLIENT_ID,
        client_secret=config.YT_CLIENT_SECRET,
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds


def post(video_path: Path, title: str, description: str) -> str:
    """Upload a local video file as a YouTube Short; returns the video ID."""
    youtube = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)

    body = {
        "snippet": {
            "title": title[:100],  # YouTube enforces a 100-char title limit
            "description": description,
            "tags": [
                "Shorts", "Sanskrit", "Bhagavad Gita", "Vedanta",
                "Upanishads", "spirituality", "Hinduism", "daily verse",
            ],
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"[gyaankhand] youtube upload: {pct}%")

    return response.get("id", "")
