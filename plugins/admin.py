"""
plugins/admin.py — Admin-only commands (broadcast, ban, etc.)
"""

import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from database import get_all_users, get_total_users, get_total_chats, get_global_stats
from config import Config

logger = logging.getLogger(__name__)


def admin_filter(_, __, message: Message):
    return message.from_user and message.from_user.id in Config.ADMIN_IDS

is_admin = filters.create(admin_filter)


@Client.on_message(filters.command("broadcast") & is_admin)
async def broadcast(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast it.")

    users = await get_all_users()
    total = len(users)
    sent = failed = 0

    prog = await message.reply_text(f"📢 Broadcasting to {total} users…")

    for user in users:
        try:
            await client.forward_messages(user["user_id"], message.chat.id, message.reply_to_message.id)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)   # rate limit safety

    await prog.edit_text(
        f"✅ **Broadcast complete**\n\n"
        f"• Sent: `{sent}`\n"
        f"• Failed: `{failed}`\n"
        f"• Total: `{total}`"
    )


@Client.on_message(filters.command("adminstat") & is_admin)
async def admin_stats(client: Client, message: Message):
    total_users = await get_total_users()
    total_chats = await get_total_chats()
    gs = await get_global_stats()

    await message.reply_text(
        "📊 **Admin Statistics**\n\n"
        f"👥 Users: `{total_users}`\n"
        f"💬 Chats: `{total_chats}`\n"
        f"🎬 Files Processed: `{gs.get('files_processed', 0)}`\n"
        f"🔍 IMDB Searches: `{gs.get('imdb_searches', 0)}`\n"
        f"🚀 Bot Starts: `{gs.get('bot_starts', 0)}`"
    )
