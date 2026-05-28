"""Instagram poster — Instagram Login (Business Login) flow.

Uses graph.instagram.com (NOT graph.facebook.com).

Two-step publish:
1. POST /{ig-user-id}/media         -> creates a Reels container, returns container ID
2. POST /{ig-user-id}/media_publish -> publishes the container

The video MUST be reachable at a public URL. We host it via raw.githubusercontent.com,
so the workflow commits the rendered video to the repo first, then triggers publish.

Token refresh:
The long-lived token lasts ~60 days. Calling /refresh_access_token before it
expires extends it for another 60 days.
"""
from __future__ import annotations

import time
from urllib.parse import quote

import requests

from . import config


def public_media_url(relpath: str) -> str:
    """Build the raw.githubusercontent.com URL for a committed file."""
    if not config.GITHUB_REPO:
        raise RuntimeError("GITHUB_REPO env var must be set, e.g. 'owner/gyaankhand'.")
    safe_path = quote(relpath.lstrip("/"))
    return (
        f"https://raw.githubusercontent.com/{config.GITHUB_REPO}/"
        f"{config.GITHUB_BRANCH}/{safe_path}"
    )


def _api_url(path: str) -> str:
    return f"{config.IG_API_HOST}/{config.IG_API_VERSION}/{path.lstrip('/')}"


def _check(resp: requests.Response, ctx: str) -> dict:
    """Raise with the API error body included; return parsed JSON on success."""
    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        raise RuntimeError(
            f"{ctx} -> HTTP {resp.status_code}: {err}"
        )
    return resp.json()


def create_media_container(video_url: str, caption: str) -> str:
    """Create a Reels media container; returns container/creation ID."""
    resp = requests.post(
        _api_url("me/media"),
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": config.IG_LONG_LIVED_TOKEN,
        },
        timeout=60,
    )
    payload = _check(resp, "create_media_container")
    container_id = payload.get("id")
    if not container_id:
        raise RuntimeError(f"No container id in response: {payload}")
    return container_id


def wait_for_container_ready(container_id: str, timeout_s: int = 300) -> None:
    """Poll container status until FINISHED or timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(
            _api_url(container_id),
            params={
                "fields": "status_code,status",
                "access_token": config.IG_LONG_LIVED_TOKEN,
            },
            timeout=30,
        )
        data = _check(resp, "wait_for_container_ready")
        status = data.get("status_code") or data.get("status", "")
        if status in ("FINISHED", "PUBLISHED"):
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} failed: {data}")
        time.sleep(3)
    raise TimeoutError(f"Container {container_id} not ready after {timeout_s}s")


def publish_container(container_id: str) -> str:
    """Publish container; returns the published media ID."""
    resp = requests.post(
        _api_url("me/media_publish"),
        data={
            "creation_id": container_id,
            "access_token": config.IG_LONG_LIVED_TOKEN,
        },
        timeout=60,
    )
    return _check(resp, "publish_container").get("id", "")


def post(video_url: str, caption: str) -> str:
    """Full happy-path for a Reel: create -> wait -> publish. Returns media ID."""
    container_id = create_media_container(video_url, caption)
    wait_for_container_ready(container_id)
    return publish_container(container_id)


def create_carousel_item(image_url: str) -> str:
    """Create a single carousel item container; returns its ID."""
    resp = requests.post(
        _api_url("me/media"),
        data={
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": config.IG_LONG_LIVED_TOKEN,
        },
        timeout=60,
    )
    payload = _check(resp, "create_carousel_item")
    item_id = payload.get("id")
    if not item_id:
        raise RuntimeError(f"No item id in response: {payload}")
    return item_id


def create_carousel_container(item_ids: list[str], caption: str) -> str:
    """Create the CAROUSEL container from a list of item IDs; returns container ID."""
    resp = requests.post(
        _api_url("me/media"),
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
            "access_token": config.IG_LONG_LIVED_TOKEN,
        },
        timeout=60,
    )
    payload = _check(resp, "create_carousel_container")
    container_id = payload.get("id")
    if not container_id:
        raise RuntimeError(f"No container id in response: {payload}")
    return container_id


def post_carousel(image_url: str, caption: str) -> str:
    """Post a single image as a 2-slide carousel. Returns media ID."""
    # Two separate item containers from the same image URL
    item_ids = [
        create_carousel_item(image_url),
        create_carousel_item(image_url),
    ]
    container_id = create_carousel_container(item_ids, caption)
    wait_for_container_ready(container_id)
    return publish_container(container_id)


def refresh_long_lived_token() -> dict:
    """Refresh the long-lived token; returns {'access_token': str, 'expires_in': int}.

    Should be called before the current token expires (every ~50 days is safe).
    """
    resp = requests.get(
        f"{config.IG_API_HOST}/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": config.IG_LONG_LIVED_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
