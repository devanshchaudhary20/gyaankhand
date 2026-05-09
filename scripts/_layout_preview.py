"""Layout-only preview: substitutes system fonts so the renderer runs in
environments without the real Noto/Crimson fonts (e.g. CI sandboxes).
Produces posts/_preview.jpg using a synthetic gradient base image.
NOT used in production — only for sanity-checking the renderer code path.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config, image_renderer  # noqa: E402

# Patch font paths to system fonts that exist in the sandbox
SYSTEM_LATO = Path("/usr/share/fonts/truetype/lato/Lato-Bold.ttf")
SYSTEM_LATO_ITALIC = Path("/usr/share/fonts/truetype/lato/Lato-Italic.ttf")
SYSTEM_LATO_REG = Path("/usr/share/fonts/truetype/lato/Lato-Regular.ttf")

if SYSTEM_LATO.exists():
    config.FONT_DEVANAGARI = SYSTEM_LATO
if SYSTEM_LATO_ITALIC.exists():
    config.FONT_IAST = SYSTEM_LATO_ITALIC
if SYSTEM_LATO_REG.exists():
    config.FONT_HANDLE = SYSTEM_LATO_REG


def make_synthetic_base(path: Path) -> None:
    """Generate a soft warm-toned base image so the overlay test is realistic."""
    w, h = 1080, 1350
    img = Image.new("RGB", (w, h), (50, 35, 25))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            r = int(80 + 60 * (y / h))
            g = int(60 + 40 * (y / h))
            b = int(40 + 20 * (y / h))
            pixels[x, y] = (r, g, b)
    # Soft vignette/blob
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((-200, 200, 800, 1100), fill=(255, 200, 100, 50))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(path, "JPEG", quality=88)


def main() -> int:
    base = config.ROOT / "data" / "base_images" / "_synthetic.jpg"
    base.parent.mkdir(parents=True, exist_ok=True)
    make_synthetic_base(base)

    # Use real Sanskrit/IAST text — Lato won't render Devanagari glyphs but the
    # IAST layout is still valid, and we can confirm wrap/overlay/positioning.
    devanagari = (
        "[Devanagari renders here in production]\n"
        "(layout test using Latin fallback)"
    )
    iast = (
        "karmaṇy-evādhikāras te mā phaleṣu kadācana |\n"
        "mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi ||"
    )
    out = config.ROOT / "posts" / "_preview.jpg"
    image_renderer.render_verse(
        base_image_path=base,
        devanagari_text=devanagari,
        iast_text=iast,
        output_path=out,
        handle="@gyaankhand",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
