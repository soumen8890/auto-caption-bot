"""
config.py — Central configuration loaded from environment variables.
Set these in Koyeb / Render dashboard or a local .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Telegram ──────────────────────────────────────────────
    API_ID: int        = int(os.environ.get("API_ID", "0"))
    API_HASH: str      = os.environ.get("API_HASH", "")
    BOT_TOKEN: str     = os.environ.get("BOT_TOKEN", "")

    # ── MongoDB Atlas ─────────────────────────────────────────
    # Format: mongodb+srv://user:pass@cluster.mongodb.net/dbname
    MONGO_URI: str     = os.environ.get("MONGO_URI", "")
    DB_NAME: str       = os.environ.get("DB_NAME", "imdb_bot")

    # ── OMDB API (free key at omdbapi.com) ────────────────────
    OMDB_KEY: str      = os.environ.get("OMDB_API_KEY", "")

    # ── TMDB API (optional — higher-res posters) ─────────────
    TMDB_KEY: str      = os.environ.get("TMDB_API_KEY", "")

    # ── Bot Behaviour ─────────────────────────────────────────
    # Comma-separated channel IDs for auto-caption, e.g. "-1001234,-1005678"
    _ch = os.environ.get("AUTO_CAPTION_CHANNELS", "")
    AUTO_CAPTION_CHANNELS: list[str] = [c.strip() for c in _ch.split(",") if c.strip()]

    # "default" | "minimal" | "full"
    DEFAULT_TEMPLATE: str = os.environ.get("CAPTION_TEMPLATE", "default")

    # Admins who can change global settings (comma-separated user IDs)
    _adm = os.environ.get("ADMIN_IDS", "")
    ADMIN_IDS: list[int] = [int(x) for x in _adm.split(",") if x.strip().isdigit()]

    MAX_CAPTION_LEN: int = 1024  # Telegram hard limit

    # ── Web server port (Render / Koyeb health-check) ─────────
    PORT: int = int(os.environ.get("PORT", "8080"))
