#!/usr/bin/env bash
# Downloads SIL OFL fonts used by the renderer.
# - Noto Sans Devanagari (variable font, Google) — for Sanskrit
# - Crimson Text Italic (Google) — for IAST transliteration
# - Noto Sans (variable font, Google) — for the @handle line

set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)/fonts"
mkdir -p "$DIR"

download() {
  local url="$1"
  local out="$2"
  if [[ -f "$out" ]]; then
    echo "[fonts] already have $(basename "$out")"
    return 0
  fi
  echo "[fonts] downloading $(basename "$out")"
  curl -fsSL "$url" -o "$out"
}

# Variable fonts from google/fonts repo. The square brackets in the filename
# are URL-encoded as %5B / %5D.
download \
  "https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth%2Cwght%5D.ttf" \
  "$DIR/NotoSansDevanagari-Bold.ttf"

download \
  "https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-Italic.ttf" \
  "$DIR/CrimsonText-Italic.ttf"

download \
  "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf" \
  "$DIR/NotoSans-Regular.ttf"

echo "[fonts] done."
