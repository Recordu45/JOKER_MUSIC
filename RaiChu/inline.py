"""
RaiChu/inline.py — Inline search with rich generated song-card thumbnails.

Behavior:
- Search YouTube (youtubesearchpython async)
- For each top result, generate a song-card image using your generator
- Upload the generated image to telegraph (https://telegra.ph/upload)
- Use returned telegraph URL as thumb_url in InlineQueryResultArticle
- Selecting a result sends "/play <videoid>" to the chat (your play handler should handle it)
"""

import asyncio
import logging
import os
import io
import uuid
import traceback
from typing import List, Optional

from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from youtubesearchpython.__future__ import VideosSearch

import aiohttp

from RaiChu.config import BOT_NAME, UPDATES_CHANNEL
from Process.ImageFont.generator import generate_song_card  # uses your uploaded font

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def _yt_search(query: str, limit: int = 6) -> List[dict]:
    try:
        s = VideosSearch(query, limit=limit)
        data = await s.next()
        items = data.get("result", []) if data else []
        out = []
        for r in items:
            vid = r.get("id") or r.get("videoId") or ""
            out.append(
                {
                    "id": vid,
                    "title": r.get("title", "Unknown Title"),
                    "duration": r.get("duration", "Unknown"),
                    "channel": (r.get("channel") or {}).get("name", "Unknown"),
                    "thumb_src": (r.get("thumbnails") or [{"url": ""}])[0].get("url", "").split("?")[0],
                }
            )
        return out
    except Exception:
        logger.exception("YouTube search failed")
        return []


async def _generate_and_upload(title: str, artist: str = "", duration: str = "", album_art: Optional[str] = None):
    """
    Generate a song card using your generator and upload to telegraph.
    Returns a public URL (https://telegra.ph/...) or None on error.
    """
    uid = uuid.uuid4().hex
    tmp_name = f"inline_{uid}.jpg"

    try:
        # generate image in a thread (generator is sync)
        await asyncio.to_thread(generate_song_card, title, artist, duration, album_art, tmp_name)

        # upload to telegra.ph using aiohttp multipart/form-data
        upload_url = "https://telegra.ph/upload"
        form = aiohttp.FormData()
        f = open(tmp_name, "rb")
        form.add_field("file", f, filename=os.path.basename(tmp_name), content_type="image/jpeg")

        async with aiohttp.ClientSession() as session:
            async with session.post(upload_url, data=form, timeout=30) as resp:
                if resp.status == 200:
                    j = await resp.json()
                    # telegraph returns a list like [{ "src": "/file/xxxx" }]
                    if isinstance(j, list) and len(j) > 0 and "src" in j[0]:
                        src = j[0]["src"]
                        # build public URL
                        public = f"https://telegra.ph{src}"
                        return public
        return None
    except Exception:
        logger.exception("Thumbnail generation/upload failed")
        return None
    finally:
        try:
            f.close()
        except Exception:
            pass
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except Exception:
            pass


def _button(videoid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Open on YouTube", url=f"https://youtu.be/{videoid}")],
        ]
    )


@Client.on_inline_query()
async def inline_handler(client: Client, query: InlineQuery):
    q = (query.query or "").strip()
    results: List[InlineQueryResultArticle] = []

    if not q:
        help_text = (
            f"🎧 {BOT_NAME} Inline Search\n\n"
            "Type a song name to search on YouTube. Select a result to send `/play <videoid>` in chat."
        )
        results.append(
            InlineQueryResultArticle(
                id="help",
                title=f"{BOT_NAME} — Inline Search",
                description="Search and play songs from YouTube",
                input_message_content=InputTextMessageContent(help_text),
            )
        )
        try:
            await query.answer(results, cache_time=30, is_personal=True)
        except Exception:
            pass
        return

    # fetch search results
    items = await _yt_search(q, limit=6)
    if not items:
        results.append(
            InlineQueryResultArticle(
                id="nores",
                title="No results found",
                description="Try another search phrase",
                input_message_content=InputTextMessageContent("No results found."),
            )
        )
        try:
            await query.answer(results, cache_time=10, is_personal=True)
        except Exception:
            pass
        return

    # For each item, generate small thumbnail and upload concurrently (but limit concurrency)
    sem = asyncio.Semaphore(3)  # limit parallel generation/uploads to 3
    async def gen_upload_task(item):
        async with sem:
            try:
                # generate and upload; pass remote thumbnail (original) as album_art for nicer cards
                public = await _generate_and_upload(item["title"], item.get("channel", ""), item.get("duration", ""), item.get("thumb_src"))
                return item, public
            except Exception:
                logger.exception("gen_upload_task failed")
                return item, None

    tasks = [asyncio.create_task(gen_upload_task(it)) for it in items]
    pairs = await asyncio.gather(*tasks)

    for item, pub in pairs:
        vid = item["id"]
        title = item["title"]
        duration = item.get("duration", "")
        channel = item.get("channel", "")
        thumb = pub or item.get("thumb_src") or None

        desc = f"{channel} • {duration}" if channel or duration else ""
        imc = InputTextMessageContent(f"/play {vid}", disable_web_page_preview=True)

        results.append(
            InlineQueryResultArticle(
                id=vid or title[:64],
                title=title[:64],
                description=desc,
                input_message_content=imc,
                thumb_url=thumb,
                reply_markup=_button(vid),
            )
        )

    # answer inline query
    try:
        await query.answer(results, cache_time=30, is_personal=True)
    except Exception:
        logger.exception("Failed to answer inline query")
        try:
            # fallback: return plain results without thumbs
            fallback = []
            for item in items:
                vid = item["id"]
                title = item["title"]
                desc = f"{item.get('channel','')} • {item.get('duration','')}"
                fallback.append(
                    InlineQueryResultArticle(
                        id=vid or title[:64],
                        title=title[:64],
                        description=desc,
                        input_message_content=InputTextMessageContent(f"/play {vid}", disable_web_page_preview=True),
                    )
                )
            await query.answer(fallback, cache_time=10, is_personal=True)
        except Exception:
            pass
