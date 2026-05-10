"""One-time script to generate a YouTube OAuth 2.0 refresh token.

Run this locally (not in CI) once to produce the credentials you'll store
as GitHub secrets.

Usage:
  1. Go to console.cloud.google.com
     - Create a project (or use an existing one)
     - Enable "YouTube Data API v3"
     - Create OAuth 2.0 credentials → Application type: Desktop app
     - Download the JSON file as client_secret.json in this repo root

  2. Run:
       python scripts/youtube_auth_setup.py

  3. A browser window will open asking you to log in with the YouTube channel
     account. Grant access.

  4. The script prints:
       YT_CLIENT_ID=...
       YT_CLIENT_SECRET=...
       YT_REFRESH_TOKEN=...

     Copy these into .env (for local use) and into GitHub secrets
     (Settings → Secrets and variables → Actions) for CI.

The refresh token does not expire unless you revoke it or the app is deleted,
so you only need to run this once.
"""
import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing dependency. Run:  pip install google-auth-oauthlib")
    sys.exit(1)

CLIENT_SECRET_FILE = Path(__file__).resolve().parent.parent / "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

if not CLIENT_SECRET_FILE.exists():
    print(f"client_secret.json not found at {CLIENT_SECRET_FILE}")
    print("Download it from console.cloud.google.com → APIs & Services → Credentials.")
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
creds = flow.run_local_server(port=0)

with CLIENT_SECRET_FILE.open() as f:
    secret_data = json.load(f)

client_id = secret_data.get("installed", secret_data.get("web", {})).get("client_id", "")
client_secret = secret_data.get("installed", secret_data.get("web", {})).get("client_secret", "")

print("\n--- Copy these into .env and GitHub secrets ---")
print(f"YT_CLIENT_ID={client_id}")
print(f"YT_CLIENT_SECRET={client_secret}")
print(f"YT_REFRESH_TOKEN={creds.refresh_token}")
