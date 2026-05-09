# gyaankhand

Daily Instagram bot that posts a verse from the Bhagavad Gita, Ashtavakra Gita,
the Bhagavata Purana, the Shaiva tradition, and the Vedas / Upanishads —
rendered onto a base image (Sanskrit Devanagari + IAST transliteration), with
the English meaning, source, and hashtags in the caption.

Runs on GitHub Actions every evening (default 7:00 PM IST). No server needed.

## How it works

1. `src/main.py render` picks an unposted verse + a random base image, renders a 1080×1350 JPG into `posts/`, and writes `state/_pending.json`.
2. The workflow commits the new image to the repo so it's served at `raw.githubusercontent.com/<repo>/<branch>/posts/...`.
3. `src/main.py publish` calls the Instagram Graph API to create a media container with that URL, polls until ready, then publishes.
4. The post is logged to `state/posted.json` so the next cycle picks a different verse.

## One-time setup

### 1. Instagram + Meta Developer

Your IG account must be Business or Creator and connected to a Facebook Page.

1. Go to <https://developers.facebook.com>, **My Apps → Create App → Business** type.
2. In the new app, **Add product → Instagram Graph API**.
3. **Tools → Graph API Explorer**, select your app, then **Add Permissions**:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `business_management`. Click **Generate Access Token** and approve.
4. The token from step 3 is short-lived. Exchange it for a long-lived one:

   ```
   GET https://graph.facebook.com/v19.0/oauth/access_token
       ?grant_type=fb_exchange_token
       &client_id={app_id}
       &client_secret={app_secret}
       &fb_exchange_token={short_lived_token}
   ```

5. Find your IDs:
   - Facebook Page ID: `GET /me/accounts` → look for your page's `id`.
   - Instagram Business Account ID: `GET /{page_id}?fields=instagram_business_account`.

You'll end up with five values to paste into GitHub Secrets (next step).

### 2. GitHub repo

```bash
cd ~/gyaankhand
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin git@github.com:<you>/gyaankhand.git
git push -u origin main
```

In the repo on GitHub:

- **Settings → Secrets and variables → Actions → New repository secret** — add each:
  - `META_APP_ID`
  - `META_APP_SECRET`
  - `META_LONG_LIVED_TOKEN`
  - `IG_BUSINESS_ACCOUNT_ID`
  - `FB_PAGE_ID`
- Same screen, **Variables** tab → add `IG_HANDLE` = `@your_handle` (optional, used in the caption signature).
- **Settings → Actions → General → Workflow permissions** → enable
  *Read and write permissions* (so the workflow can push the rendered image and updated state back).

### 3. Base images

Drop 10–20 portrait JPG/PNG images into `data/base_images/`. Recommended:

- 1080×1350 or larger, will be center-cropped.
- Soft, low-detail aesthetic (skies, mountains, temples, lotuses, blurred bokeh).
- High-detail busy images will fight the text overlay.

### 4. Local test (recommended before pushing)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/download_fonts.sh
python -m src.main render --dry-run
open posts/*.jpg   # macOS — confirm the layout looks right
```

### 5. First scheduled run

Once everything is pushed and secrets are set, you can trigger a manual run from the **Actions** tab → *Daily Instagram Post* → *Run workflow*. After it succeeds, the daily 7:00 PM IST cron takes over.

## Adjusting the schedule

Edit `.github/workflows/post.yml` — the `cron` field uses UTC. Quick reference:

| Local time (IST) | UTC cron      |
| ---------------- | ------------- |
| 6:30 PM          | `0 13 * * *`  |
| 7:00 PM          | `30 13 * * *` |
| 8:00 PM          | `30 14 * * *` |

Use <https://crontab.guru> for other timezones.

## Adding more verses

Append to `data/verses.json`. Each entry needs:

```json
{
  "id": "unique-id",
  "text_devanagari": "देवनागरी text\nwith line breaks",
  "text_iast": "IAST transliteration\nwith line breaks",
  "translation_en": "English meaning for the caption.",
  "source": "Source citation, e.g. Bhagavad Gita 2.47",
  "tags": ["optional", "tags"]
}
```

A scraper that bulk-imports from public-domain sources is on the to-do list — for now, the curated set will rotate through ~3 weeks before repeating.

## Token rotation

Long-lived tokens last ~60 days. To rotate, repeat step 4 of the Meta setup with a fresh short-lived token, then update the `META_LONG_LIVED_TOKEN` secret in GitHub. (Auto-refresh is on the to-do list.)

## Troubleshooting

- **Workflow fails at "Publish": `(#10) Application does not have permission for this action`** — your access token is missing one of the scopes. Regenerate with all five.
- **Workflow fails at "Publish": `Media container ERROR`** — usually the image URL isn't reachable. Confirm the commit + push step ran and the image is visible at `https://raw.githubusercontent.com/<repo>/<branch>/posts/<filename>.jpg`.
- **Sanskrit renders as boxes** — the Devanagari font didn't download. Re-run `bash scripts/download_fonts.sh` and check `fonts/`.
- **Two posts in one day** — the schedule fired and you also pushed a commit that triggered a separate run. Use `[skip ci]` in commit messages, which the workflow already does for its automated commits.
