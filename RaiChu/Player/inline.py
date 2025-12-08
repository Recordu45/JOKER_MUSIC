# RaiChu/Player/inline.py

import logging
from youtubesearchpython import VideosSearch
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from pyrogram import filters
from Process.main import bot   # IMPORTANT: use bot instance

log = logging.getLogger(__name__)


# ---------- YouTube search helper ----------
def ytsearch(query: str):
    try:
        search = VideosSearch(query, limit=1).result()
        if not search["result"]:
            return None

        data = search["result"][0]
        return {
            "title": data.get("title"),
            "url": data.get("link"),
            "duration": data.get("duration") or "Unknown",
            "thumbnail": f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg",
            "videoid": data["id"],
        }
    except Exception as e:
        log.exception("ytsearch error: %s", e)
        return None


# ---------- INLINE HANDLER ----------
@bot.on_inline_query()
async def inline_handler(client, query: InlineQuery):

    search_text = query.query.lower().strip()

    # ---------- 1) Quick control buttons (empty query) ----------
    if search_text == "":
        controls = [
            InlineQueryResultArticle(
                title="Pause Stream",
                description="Pause the current stream.",
                thumb_url="https://telegra.ph/file/c0a1c789def7b93f13745.png",
                input_message_content=InputTextMessageContent("/pause"),
            ),
            InlineQueryResultArticle(
                title="Resume Stream",
                description="Resume the stream.",
                thumb_url="https://telegra.ph/file/02d1b7f967ca11404455a.png",
                input_message_content=InputTextMessageContent("/resume"),
            ),
            InlineQueryResultArticle(
                title="Mute Stream",
                description="Mute the stream.",
                thumb_url="https://telegra.ph/file/66516f2976cb6d87e20f9.png",
                input_message_content=InputTextMessageContent("/mute"),
            ),
            InlineQueryResultArticle(
                title="Unmute Stream",
                description="Unmute the stream.",
                thumb_url="https://telegra.ph/file/3078794f9341ffd582e18.png",
                input_message_content=InputTextMessageContent("/unmute"),
            ),
            InlineQueryResultArticle(
                title="Skip Stream",
                description="Skip to the next track.",
                thumb_url="https://telegra.ph/file/98b88e52bc625903c7a2f.png",
                input_message_content=InputTextMessageContent("/skip"),
            ),
            InlineQueryResultArticle(
                title="End Stream",
                description="Stop the stream.",
                thumb_url="https://telegra.ph/file/d2eb03211baaba8838cc4.png",
                input_message_content=InputTextMessageContent("/stop"),
            ),
        ]

        return await client.answer_inline_query(
            query.id,
            results=controls,
            switch_pm_text="Search a song or video on YouTube...",
            switch_pm_parameter="inline",
            cache_time=1,
        )

    # ---------- 2) User searched something: YouTube Search ----------
    result = ytsearch(search_text)

    if not result:
        return await client.answer_inline_query(
            query.id,
            results=[],
            switch_pm_text="No results found. Try another search.",
            switch_pm_parameter="notfound",
            cache_time=1,
        )

    title = result["title"]
    url = result["url"]
    videoid = result["videoid"]
    duration = result["duration"]
    thumbnail = result["thumbnail"]

    # Result card → sends /play <url>
    result_card = InlineQueryResultArticle(
        title=f"{title}",
        description=f"Duration: {duration}",
        thumb_url=thumbnail,
        input_message_content=InputTextMessageContent(f"/play {url}"),
    )

    return await client.answer_inline_query(
        query.id,
        results=[result_card],
        cache_time=1,
    )
