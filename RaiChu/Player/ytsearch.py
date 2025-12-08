# RaiChu/Player/ytsearch.py

import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from youtube_search import YoutubeSearch
from Process.filters import command, other_filters
from RaiChu.config import BOT_USERNAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@Client.on_message(command(["search", f"search@{BOT_USERNAME}"]) & ~filters.edited & other_filters)
async def ytsearch_handler(_, message: Message):

    # Close button
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🗑 Close", callback_data="cls")]]
    )

    # Check argument
    if len(message.command) < 2:
        return await message.reply_text("⚠ Please enter something to search.\n\nExample:\n`/search Believer`")

    query = message.text.split(None, 1)[1]
    status = await message.reply_text("🔎 Searching YouTube...")

    try:
        # Perform search
        results = YoutubeSearch(query, max_results=5).to_dict()

        if len(results) == 0:
            return await status.edit("❌ No results found.", reply_markup=keyboard)

        text = ""
        for item in results:
            title = item.get("title", "No title")
            duration = item.get("duration", "Unknown")
            views = item.get("views", "Unknown")
            channel = item.get("channel", "Unknown")
            link = "https://www.youtube.com" + item.get("url_suffix", "")

            text += (
                f"🎵 **{title}**\n"
                f"⏱ Duration: `{duration}`\n"
                f"👀 Views: `{views}`\n"
                f"📺 Channel: {channel}\n"
                f"🔗 {link}\n\n"
            )

        await status.edit(
            text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        await status.edit(f"❌ Error while searching:\n`{e}`")
