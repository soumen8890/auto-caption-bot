"""
main.py — Entry point.
Starts the Pyrogram bot + a tiny aiohttp health-check server
so Koyeb / Render know the service is alive.
"""

import asyncio
import logging
import importlib
import os
from aiohttp import web
from pyrogram import Client
from config import Config
from database import connect_db, close_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────── Pyrogram Client ────────────

app = Client(
    name="imdb_caption_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"),        # auto-loads plugins/*.py
    sleep_threshold=60,
    workers=8,
)

# ──────────── Health-check server ────────────

async def health(request):
    return web.Response(text="OK", status=200)


async def start_webserver():
    server = web.Application()
    server.router.add_get("/", health)
    server.router.add_get("/health", health)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    logger.info("Health-check server listening on port %s", Config.PORT)


# ──────────── Lifecycle ────────────

async def main():
    await connect_db()
    await start_webserver()

    async with app:
        me = await app.get_me()
        logger.info("🤖 Bot running as @%s (id=%s)", me.username, me.id)
        await asyncio.Event().wait()   # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down…")
    finally:
        asyncio.run(close_db())
