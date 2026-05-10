"""Renders a verse onto a base image and saves to posts/."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config


def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    if not path.exists():
        raise FileNotFoundError(
            f"Font not found at {path}. Run scripts/download_fonts.sh first."
        )
    return ImageFont.truetype(str(path), size)


def _wrap_to_width(
    text_block: str,
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
    max_width: int,
) -> list[str]:
    """Wrap each input line to fit max_width, preserving intentional line breaks."""
    out: list[str] = []
    for paragraph in text_block.split("\n"):
        if not paragraph.strip():
            out.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for w in words:
            candidate = (current + " " + w).strip()
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = candidate
            else:
                if current:
                    out.append(current)
                current = w
        if current:
            out.append(current)
    return out


def _measure_block(
    lines: Iterable[str],
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
    line_spacing: int,
) -> tuple[int, int]:
    """Returns (width, height) of the rendered block."""
    lines = list(lines)
    if not lines:
        return 0, 0
    max_w = 0
    total_h = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line or " ", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += h
        if i < len(lines) - 1:
            total_h += line_spacing
    return max_w, total_h


def _draw_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    center_x: int,
    top_y: int,
    line_spacing: int,
    fill: tuple[int, int, int],
) -> int:
    """Draws lines centered horizontally; returns the y after the last line."""
    y = top_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line or " ", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = center_x - w // 2
        # Subtle shadow for readability over photo
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=fill)
        y += h + line_spacing
    return y


def _prepare_base(image_path: Path) -> Image.Image:
    """Open base image, fit to (W, H) with center crop."""
    img = Image.open(image_path).convert("RGB")
    target_ratio = config.IMG_WIDTH / config.IMG_HEIGHT
    src_ratio = img.width / img.height
    if src_ratio > target_ratio:
        # Source is wider; crop sides
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Source is taller; crop top/bottom
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))
    img = img.resize((config.IMG_WIDTH, config.IMG_HEIGHT), Image.LANCZOS)
    # A subtle blur softens busy backgrounds for text readability
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    return img


def render_verse(
    base_image_path: Path,
    devanagari_text: str,
    iast_text: str,
    output_path: Path,
    handle: str | None = None,
) -> Path:
    """Render the post image and save to output_path. Returns output_path."""
    base = _prepare_base(base_image_path)

    # Translucent orange overlay for warmth + text legibility
    overlay = Image.new(
        "RGBA",
        (config.IMG_WIDTH, config.IMG_HEIGHT),
        (*config.OVERLAY_COLOR, config.OVERLAY_OPACITY),
    )
    composite = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(composite)

    devanagari_font = _load_font(config.FONT_DEVANAGARI, config.DEVANAGARI_FONT_SIZE)
    iast_font = _load_font(config.FONT_IAST, config.IAST_FONT_SIZE)

    max_text_width = config.IMG_WIDTH - 2 * config.SIDE_PADDING

    # Wrap blocks
    devanagari_lines = _wrap_to_width(devanagari_text, devanagari_font, draw, max_text_width)
    iast_lines = _wrap_to_width(iast_text, iast_font, draw, max_text_width)

    # Measure for vertical centering
    _, dev_h = _measure_block(devanagari_lines, devanagari_font, draw, config.LINE_SPACING_DEVANAGARI)
    _, iast_h = _measure_block(iast_lines, iast_font, draw, config.LINE_SPACING_IAST)
    total_h = dev_h + config.GAP_BETWEEN_BLOCKS + iast_h

    start_y = max(120, (config.IMG_HEIGHT - total_h) // 2)
    center_x = config.IMG_WIDTH // 2

    after_dev = _draw_block(
        draw,
        devanagari_lines,
        devanagari_font,
        center_x,
        start_y,
        config.LINE_SPACING_DEVANAGARI,
        config.TEXT_COLOR,
    )
    _draw_block(
        draw,
        iast_lines,
        iast_font,
        center_x,
        after_dev + config.GAP_BETWEEN_BLOCKS,
        config.LINE_SPACING_IAST,
        config.TEXT_COLOR,
    )

    # Optional handle at the bottom
    if handle:
        try:
            handle_font = _load_font(config.FONT_HANDLE, config.HANDLE_FONT_SIZE)
            bbox = draw.textbbox((0, 0), handle, font=handle_font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x = (config.IMG_WIDTH - w) // 2
            y = config.IMG_HEIGHT - h - 50
            draw.text((x + 1, y + 1), handle, font=handle_font, fill=(0, 0, 0))
            draw.text((x, y), handle, font=handle_font, fill=config.HANDLE_COLOR)
        except FileNotFoundError:
            pass  # handle font is optional

    output_path.parent.mkdir(parents=True, exist_ok=True)
    composite.convert("RGB").save(output_path, "JPEG", quality=92, optimize=True)
    return output_path
