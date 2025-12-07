# Joker/inline.py
from typing import Optional
import logging

from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from youtubesearchpython.__future__ import VideosSearch

from Joker.config import BOT_NAME, UPDATES_CHANNEL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def ytsearch(query: str) -> Optional[dict]:
    """
    Async YouTube search for a single top result.
    Returns a dict: { title, link, duration, thumbnail, id } or None.
    """
    try:
        search = VideosSearch(query, limit=1)
        data = await search.next()
        if not data or "result" not in data or not data["result"]:
            return None
        d = data["result"][0]
        vid = d.get("id") or d.get("videoId") or ""
        return {
            "title": d.get("title", "Unknown Title"),
            "link": d.get("link") or f"https://www.youtube.com/watch?v={vid}",
            "duration": d.get("duration", "Unknown"),
            "thumbnail": (d.get("thumbnails") or [{"url": ""}])[0].get("url", "").split("?")[0],
            "id": vid,
        }
    except Exception as e:
        logger.exception("ytsearch error: %s", e)
        return None


def audio_markup(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="• Mᴇɴᴜ", callback_data=f"cbmenu | {user_id}"),
            InlineKeyboardButton(text="• Iɴʟɪɴᴇ", switch_inline_query_current_chat=""),
        ],
        [InlineKeyboardButton(text="• Cʟᴏsᴇ", callback_data="cls")],
    ]
    return InlineKeyboardMarkup(buttons)


def stream_markup(user_id: int, dlurl: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="⏸", callback_data=f"cbpause | {user_id}"),
            InlineKeyboardButton(text="⏯", callback_data=f"cbresume | {user_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"cbskip | {user_id}"),
            InlineKeyboardButton(text="⏹", callback_data=f"cbstop | {user_id}"),
        ],
        [
            InlineKeyboardButton(text="• ᴍᴇɴᴜ •", switch_inline_query_current_chat=""),
            InlineKeyboardButton(text="• ʏᴏᴜᴛᴜʙᴇ •", url=f"{dlurl}"),
        ],
        [InlineKeyboardButton(text="ᴄʟᴏsᴇ", callback_data="cls")],
    ]
    return InlineKeyboardMarkup(buttons)


def menu_markup(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="⏸", callback_data=f"cbpause | {user_id}"),
            InlineKeyboardButton(text="⏯", callback_data=f"cbresume | {user_id}"),
        ],
        [
            InlineKeyboardButton(text="⏭", callback_data=f"cbskip | {user_id}"),
            InlineKeyboardButton(text="⏹", callback_data=f"cbstop | {user_id}"),
        ],
        [
            InlineKeyboardButton(text="🔇", callback_data=f"cbmute | {user_id}"),
            InlineKeyboardButton(text="ᴜᴩᴅᴀᴛᴇs", url=f"https://t.me/{UPDATES_CHANNEL}" if UPDATES_CHANNEL else "https://t.me/BotDuniyaXd"),
            InlineKeyboardButton(text="🔊", callback_data=f"cbunmute | {user_id}"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def song_download_markup(videoid: str) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="⬇️ ᴀᴜᴅɪᴏ", callback_data=f"gets audio|{videoid}"),
            InlineKeyboardButton(text="⬇️ ᴠɪᴅᴇᴏ", callback_data=f"gets video|{videoid}"),
        ],
        [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="cbhome")],
    ]
    return InlineKeyboardMarkup(buttons)


close_mark = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="cls")]])

back_mark = InlineKeyboardMarkup([[InlineKeyboardButton("• ʙᴀᴄᴋ •", callback_data="cbmenu")]])
