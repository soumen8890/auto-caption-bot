"""
plugins/search.py — /search command and IMDB inline result callbacks.
"""

import os
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from imdb_helper import IMDBHelper
from caption_template import generate_caption
from database import increment_global
from utils import download_image, save_thumbnail

imdb = IMDBHelper()


@Client.on_message(filters.command("search"))
async def search_cmd(client: Client, message: Message):
    query = " ".join(message.command[1:]).strip()
    if not query:
        return await message.reply_text("Usage: `/search <movie or show title>`")

    msg = await message.reply_text(f"🔍 Searching IMDB for: **{query}**…")
    await increment_global("imdb_searches")

    results = await imdb.search(query)
    if not results:
        return await msg.edit_text("❌ No IMDB results found.")

    buttons = []
    for r in results[:6]:
        label = f"{'🎬' if r.get('type') == 'movie' else '📺'} {r['title']} ({r.get('year','?')})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"show_{r['imdb_id']}")])

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_search")])
    await msg.edit_text("**IMDB Search Results — tap to view:**", reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^show_(.+)$"))
async def show_imdb(client: Client, cb: CallbackQuery):
    imdb_id = cb.data.split("_", 1)[1]
    await cb.answer("Fetching…")
    await cb.message.edit_text("⏳ Loading IMDB data…")

    info = await imdb.get_by_id(imdb_id)
    if not info:
        return await cb.message.edit_text("❌ Failed to fetch IMDB data.")

    caption = generate_caption(info)
    poster_url = info.get("poster")
    thumb_path = None

    if poster_url:
        img_bytes = await download_image(poster_url)
        if img_bytes:
            thumb_path = save_thumbnail(img_bytes, f"/tmp/search_{imdb_id}.jpg")

    try:
        if thumb_path:
            await cb.message.reply_photo(photo=thumb_path, caption=caption, parse_mode="markdown")
            os.remove(thumb_path)
        else:
            await cb.message.reply_text(caption, parse_mode="markdown")
        await cb.message.delete()
    except Exception as e:
        await cb.message.edit_text(f"❌ Error: `{e}`")


@Client.on_callback_query(filters.regex(r"^cancel_search$"))
async def cancel_search(client: Client, cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer("Cancelled.")
