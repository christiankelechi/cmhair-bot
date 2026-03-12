"""
cmhair-bot configuration.
Copy .env.example → .env and fill in your values.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ─────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]

# Comma-separated list of allowed Telegram chat IDs (admin users).
# Leave blank to allow all users (not recommended for production).
_raw_ids = os.getenv("TELEGRAM_ADMIN_CHAT_IDS", "")
TELEGRAM_ADMIN_CHAT_IDS: set[int] = (
    {int(x.strip()) for x in _raw_ids.split(",") if x.strip()}
    if _raw_ids.strip()
    else set()
)

# ── Backend API ───────────────────────────────────────────────────────────────
API_BASE_URL: str = os.getenv(
    "API_BASE_URL", ""
).rstrip("/")

ADMIN_EMAIL: str = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD: str = os.environ["ADMIN_PASSWORD"]
