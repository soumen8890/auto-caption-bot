"""
plugins/start.py — /start, /help commands.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, increment_global, get_total_users, get_total_chats, get_global_stats
from config import Config


@Client.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await get_user(message.from_user.id)          # register user
    await increment_global("bot_starts")

    await message.reply_text(
        f"👋 **Welcome, {message.from_user.first_name}!**\n\n"
        "I auto-detect movie/show names from filenames, fetch **IMDB** data,\n"
        "replace your media thumbnail with the **official poster**, and add a\n"
        "rich formatted **caption** — all automatically!\n\n"
        "**📤 Just send or forward any video/document file.**\n\n"
        "**Commands:**\n"
        "`/search <title>` — Search IMDB\n"
        "`/settings` — Your caption preferences\n"
        "`/stats` — Bot statistics\n"
        "`/help` — Full guide",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Channel", url="https://t.me/yourchannel"),
            InlineKeyboardButton("💬 Support", url="https://t.me/yoursupport"),
        ], [
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true"),
        ]]),
    )


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(
        "📖 **Help Guide**\n\n"
        "**🔹 Auto Mode**\n"
        "Send any video/document — the bot reads the filename automatically.\n\n"
        "**🔹 Manual Override**\n"
        "Reply to a file with `/caption Batman 2022` to force a specific title.\n\n"
        "**🔹 IMDB Search**\n"
        "`/search Oppenheimer` — browse results with inline buttons.\n\n"
        "**🔹 Settings**\n"
        "`/settings` — switch between `default`, `minimal`, `full` caption templates.\n\n"
        "**🔹 Supported formats**\n"
        "`.mkv` `.mp4` `.avi` `.mov` `.ts` `.m4v` `.wmv` `.webm`\n\n"
        "**🔹 Channel / Group**\n"
        "Add me as admin with **Post Messages** permission for auto-caption."
    )


@Client.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    total_users = await get_total_users()
    total_chats = await get_total_chats()
    gs = await get_global_stats()

    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"💬 **Total Chats:** `{total_chats}`\n"
        f"🎬 **Files Processed:** `{gs.get('files_processed', 0)}`\n"
        f"🔍 **IMDB Searches:** `{gs.get('imdb_searches', 0)}`\n"
        f"🚀 **Bot Starts:** `{gs.get('bot_starts', 0)}`"
    )
