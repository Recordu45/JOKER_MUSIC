# RaiChu/Player/Group.py
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from time import time

from Process.main import bot      # IMPORTANT: bind handlers to your bot instance
from Process.filters import command, other_filters2
from Process.decorators import authorized_users_only
from RaiChu.config import (
    ASSISTANT_NAME,
    BOT_NAME,
    BOT_USERNAME,
    GROUP_SUPPORT,
    OWNER_NAME,
    UPDATES_CHANNEL,
)

# Bot uptime tracking
START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()

TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60 * 60 * 24),
    ("hour", 60 * 60),
    ("min", 60),
    ("sec", 1),
)

async def _human_time_duration(seconds):
    if seconds <= 0:
        return "0 sec"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append(f"{amount} {unit}{'' if amount == 1 else 's'}")
    return ", ".join(parts)


# ====================== UPTIME ======================
@bot.on_message(command(["uptime", f"uptime@{BOT_USERNAME}"]) & ~filters.edited)
@authorized_users_only
async def get_uptime(_, message: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(uptime_sec)
    await message.reply_text(
        "🤖 **RAICHU BOT STATUS**\n"
        f"➤ **Uptime:** `{uptime}`\n"
        f"➤ **Started at:** `{START_TIME_ISO}`"
    )


# ====================== PING ======================
@bot.on_message(command(["ping", f"ping@{BOT_USERNAME}"]) & ~filters.edited)
async def ping_pong(_, message: Message):
    start = time()
    m = await message.reply_text("Pinging...")
    delta = (time() - start) * 1000
    await m.edit_text(f"🏓 **Pong!**\n`{delta:.2f} ms`")


# ====================== START (GROUPS) ======================
@bot.on_message(command(["start", f"start@{BOT_USERNAME}"]) & filters.group)
async def start(_, message: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(uptime_sec)

    await message.reply_text(
        f"✔ **Bot is Active**\n"
        f"➤ **Uptime:** `{uptime}`",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("☢ Group", url=f"https://t.me/{GROUP_SUPPORT}"),
                    InlineKeyboardButton("📣 Channel", url=f"https://t.me/{UPDATES_CHANNEL}")
                ]
            ]
        )
    )


# ====================== HELP ======================
@bot.on_message(command(["help", f"help@{BOT_USERNAME}"]) & filters.group)
async def help(_, message: Message):
    await message.reply_text(
        f"👋 Hello {message.from_user.mention()}!\n"
        f"Click the button below to see how to use this bot.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="📘 How to Use Me",
                        url=f"https://t.me/{BOT_USERNAME}?start=help"
                    )
                ]
            ]
        )
    )
