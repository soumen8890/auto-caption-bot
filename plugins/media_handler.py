"""
plugins/media_handler.py — Core logic:
  1. Receive video/document
  2. Parse filename → search IMDB → fetch details
  3. Download IMDB poster → resize as thumbnail
  4. Re-upload file with new thumbnail + rich caption
"""

import os
import re
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from imdb_helper import IMDBHelper
from caption_template import generate_caption
from database import get_user, increment_user_stat, increment_global
from utils import parse_filename, is_media_file, download_image, save_thumbnail, human_size
from config import Config

logger = logging.getLogger(__name__)
imdb   = IMDBHelper()

# ──────────── Filters ────────────

MEDIA_FILTER = filters.private & (filters.video | filters.document | filters.audio)
CHANNEL_FILTER = (filters.channel | filters.group) & (filters.video | filters.document)


# ──────────── Core processor ────────────

async def process_media(client: Client, message: Message, forced_title: str = None):
    """Shared processor for private, group, and channel messages."""

    # Identify media object + filename
    if message.video:
        media = message.video
        filename = media.file_name or f"video_{media.file_unique_id}.mp4"
        send_fn = client.send_video
        send_kw = {"supports_streaming": True}
    elif message.document:
        media = message.document
        filename = media.file_name or f"doc_{media.file_unique_id}"
        send_fn = client.send_document
        send_kw = {}
    elif message.audio:
        media = message.audio
        filename = media.file_name or f"audio_{media.file_unique_id}.mp3"
        send_fn = client.send_audio
        send_kw = {}
    else:
        return

    # Skip non-video documents
    if message.document and not is_media_file(filename):
        return

    # Determine title
    if forced_title:
        title, year = forced_title, None
    else:
        title, year = parse_filename(filename)

    if not title:
        return await message.reply_text(
            "⚠️ **Couldn't detect title.**\n"
            "Reply to a file with `/caption <title> <year>` to set it manually."
        )

    # Get user settings
    user_id  = message.from_user.id if message.from_user else 0
    user     = await get_user(user_id) if user_id else {"template": Config.DEFAULT_TEMPLATE}
    template = user.get("template", Config.DEFAULT_TEMPLATE)

    # ── Status message ──
    status = await message.reply_text(
        f"🔍 Searching IMDB for **{title}**" + (f" ({year})" if year else "") + "…"
    )

    results = await imdb.search(title, year=year)
    if not results:
        await status.edit_text(
            f"❌ No IMDB results for **{title}**.\n"
            "Use `/caption <correct title>` and resend the file.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Search manually", switch_inline_query_current_chat=title)
            ]])
        )
        return

    await status.edit_text("📡 Fetching IMDB details…")
    info = await imdb.get_by_id(results[0]["imdb_id"])
    if not info:
        await status.edit_text("⚠️ IMDB fetch failed. Sending with basic caption…")
        info = {"title": title, "year": year}

    # ── Download original file ──
    await status.edit_text("📥 Downloading file…")
    try:
        file_path = await _download_with_retry(client, message)
    except Exception as e:
        return await status.edit_text(f"❌ Download failed: `{e}`")

    # ── Download IMDB poster as thumbnail ──
    thumb_path = None
    if info.get("poster"):
        img_bytes = await download_image(info["poster"])
        if img_bytes:
            thumb_path = save_thumbnail(img_bytes, f"/tmp/thumb_{media.file_unique_id}.jpg")

    caption = generate_caption(info, filename=filename, template=template)

    # ── Re-upload ──
    await status.edit_text("📤 Uploading with IMDB thumbnail & caption…")
    try:
        await send_fn(
            message.chat.id,
            file_path,
            caption=caption,
            parse_mode="markdown",
            thumb=thumb_path,
            **send_kw,
        )
        await status.delete()

        # ── Update stats ──
        await increment_user_stat(user_id)
        await increment_global("files_processed")

    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        await status.edit_text("⚠️ Flood wait hit. Please try again shortly.")
    except Exception as e:
        logger.error("Upload error: %s", e)
        await status.edit_text(f"❌ Upload error: `{e}`")
    finally:
        for p in (file_path, thumb_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


async def _download_with_retry(client: Client, message: Message, retries: int = 3) -> str:
    path = f"/tmp/media_{message.id}"
    for attempt in range(retries):
        try:
            return await client.download_media(message, file_name=path)
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except Exception as e:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(3)
    raise RuntimeError("Download failed after retries")


# ──────────── Handlers ────────────

@Client.on_message(MEDIA_FILTER)
async def handle_private_media(client: Client, message: Message):
    user = await get_user(message.from_user.id)
    if not user.get("auto_caption", True):
        return
    await process_media(client, message)


@Client.on_message(filters.command("caption") & filters.reply)
async def handle_manual_caption(client: Client, message: Message):
    """Reply to a media file with /caption <title> to override auto-detection."""
    title = " ".join(message.command[1:]).strip()
    if not title:
        return await message.reply_text("Usage: reply to a file with `/caption <title> <year>`")

    replied = message.reply_to_message
    if not (replied and (replied.video or replied.document or replied.audio)):
        return await message.reply_text("⚠️ Reply to a video or document file.")

    await process_media(client, replied, forced_title=title)


@Client.on_message(CHANNEL_FILTER & filters.incoming)
async def handle_channel_media(client: Client, message: Message):
    """Auto-caption media in whitelisted channels/groups."""
    if str(message.chat.id) not in Config.AUTO_CAPTION_CHANNELS:
        return
    await process_media(client, message)
