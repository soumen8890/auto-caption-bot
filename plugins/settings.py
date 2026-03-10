"""
plugins/settings.py — Per-user and per-chat settings via inline keyboard.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, update_user, get_chat, update_chat


def _settings_keyboard(template: str, auto: bool) -> InlineKeyboardMarkup:
    def mark(t): return f"✅ {t}" if template == t else t
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(mark("default"),  callback_data="tmpl_default"),
            InlineKeyboardButton(mark("minimal"),  callback_data="tmpl_minimal"),
            InlineKeyboardButton(mark("full"),     callback_data="tmpl_full"),
        ],
        [
            InlineKeyboardButton(
                f"🔔 Auto-Caption: {'ON ✅' if auto else 'OFF ❌'}",
                callback_data="toggle_auto"
            )
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close_settings")],
    ])


@Client.on_message(filters.command("settings"))
async def settings_cmd(client: Client, message: Message):
    user = await get_user(message.from_user.id)
    template = user.get("template", "default")
    auto     = user.get("auto_caption", True)

    await message.reply_text(
        "⚙️ **Your Settings**\n\n"
        "**Caption Template** — choose the info density:\n"
        "• `default` — rating, genre, director, cast, short plot\n"
        "• `minimal` — one-liner summary\n"
        "• `full` — everything including RT, Metacritic, awards\n\n"
        "**Auto-Caption** — toggle whether files are processed automatically.",
        reply_markup=_settings_keyboard(template, auto)
    )


@Client.on_callback_query(filters.regex(r"^tmpl_(default|minimal|full)$"))
async def set_template(client: Client, cb: CallbackQuery):
    tmpl = cb.data.split("_", 1)[1]
    await update_user(cb.from_user.id, {"template": tmpl})
    user = await get_user(cb.from_user.id)
    await cb.answer(f"Template set to: {tmpl}", show_alert=False)
    await cb.message.edit_reply_markup(
        _settings_keyboard(tmpl, user.get("auto_caption", True))
    )


@Client.on_callback_query(filters.regex(r"^toggle_auto$"))
async def toggle_auto(client: Client, cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    new_val = not user.get("auto_caption", True)
    await update_user(cb.from_user.id, {"auto_caption": new_val})
    tmpl = user.get("template", "default")
    await cb.answer(f"Auto-Caption {'enabled' if new_val else 'disabled'}")
    await cb.message.edit_reply_markup(_settings_keyboard(tmpl, new_val))


@Client.on_callback_query(filters.regex(r"^close_settings$"))
async def close_settings(client: Client, cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer()
