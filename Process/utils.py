import os
import logging
import asyncio
import traceback
from typing import Optional, Tuple, Union

from Process.main import bot, call_py
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from Process.queues import get_queue, pop_an_item, clear_queue
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo,
)
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pytgcalls.types.stream import StreamAudioEnded

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="• Mᴇɴᴜ", callback_data="cbmenu"),
            InlineKeyboardButton(text="• Cʟᴏsᴇ", callback_data="cls"),
        ]
    ]
)


def _normalize_item(item: Union[list, dict]) -> dict:
    """
    Normalize a queue item to a dict with keys:
      title, link, ref, type, quality
    Supports legacy list style [songname, link, ref, type, quality].
    """
    if item is None:
        return {}
    if isinstance(item, dict):
        return {
            "title": item.get("title") or item.get("songname") or "",
            "link": item.get("link") or "",
            "ref": item.get("ref"),
            "type": item.get("type") or item.get("media_type") or "Audio",
            "quality": item.get("quality") or item.get("Q") or 0,
        }
    # legacy list/tuple
    try:
        return {
            "title": item[0],
            "link": item[1],
            "ref": item[2] if len(item) > 2 else None,
            "type": item[3] if len(item) > 3 else "Audio",
            "quality": item[4] if len(item) > 4 else 0,
        }
    except Exception:
        return {"title": "", "link": "", "ref": None, "type": "Audio", "quality": 0}


def _quality_obj(q) -> Tuple:
    """
    Return (audio_obj, video_quality_obj) based on numeric quality.
    """
    audio = HighQualityAudio()
    if q in (720, "720"):
        return audio, HighQualityVideo()
    if q in (480, "480"):
        return audio, MediumQualityVideo()
    if q in (360, "360"):
        return audio, LowQualityVideo()
    # fallback
    return audio, HighQualityVideo()


async def skip_current_song(chat_id: int) -> Union[int, list]:
    """
    Skip the current song and start the next one.
    Returns:
      - 1 if queue emptied and bot left the vc
      - 2 if error occurred and bot left
      - [title, link, type] if next song started successfully
      - 0 if no queue present
    """
    try:
        q = get_queue(chat_id)
        if not q:
            return 0

        if len(q) == 1:
            # nothing to play next
            await call_py.leave_group_call(chat_id)
            clear_queue(chat_id)
            return 1

        # get the next item (index 1 because index 0 is current)
        next_item = _normalize_item(q[1])
        title = next_item["title"]
        stream_url = next_item["link"]
        media_type = next_item["type"]
        quality = next_item["quality"]

        # select stream based on type
        if media_type.lower() == "audio":
            await call_py.change_stream(chat_id, AudioPiped(stream_url))
        else:
            audio_obj, video_obj = _quality_obj(quality)
            await call_py.change_stream(chat_id, AudioVideoPiped(stream_url, audio_obj, video_obj))

        # pop the current (index 0)
        popped = pop_an_item(chat_id)
        return [title, stream_url, media_type]
    except Exception:
        logger.exception("Error while skipping to next song in chat %s", chat_id)
        try:
            await call_py.leave_group_call(chat_id)
        except Exception:
            logger.exception("Error leaving group call for chat %s", chat_id)
        clear_queue(chat_id)
        return 2


async def skip_item(chat_id: int, index: int) -> Union[str, int]:
    """
    Remove an item at position `index` from the queue (0-based).
    Returns the removed song title or 0 on failure.
    """
    try:
        q = get_queue(chat_id)
        if not q:
            return 0
        # if legacy list style, operate carefully
        if index < 0 or index >= len(q):
            return 0
        item = q.pop(index)
        # if you removed the current (index 0) we should advance the stream
        if index == 0:
            # try to start next automatically
            await skip_current_song(chat_id)
        normalized = _normalize_item(item)
        return normalized.get("title", "") or 0
    except Exception:
        logger.exception("Error removing item %s from queue %s", index, chat_id)
        return 0


# --- PyTgCalls event handlers ---


@call_py.on_kicked()
async def _kicked_handler(_, chat_id: int):
    clear_queue(chat_id)


@call_py.on_closed_voice_chat()
async def _closed_voice_chat_handler(_, chat_id: int):
    clear_queue(chat_id)


@call_py.on_left()
async def _left_handler(_, chat_id: int):
    clear_queue(chat_id)


@call_py.on_stream_end()
async def _stream_end_handler(_, u: Update):
    """
    Handle StreamAudioEnded events by starting the next track (if any)
    and notifying the chat.
    """
    try:
        if isinstance(u, StreamAudioEnded):
            chat_id = u.chat_id
            logger.info("Stream ended in chat %s", chat_id)
            res = await skip_current_song(chat_id)
            if res == 1:
                # left because no next
                await bot.send_message(chat_id, "✅ **userbot has disconnected from video chat.**")
            elif res == 2:
                await bot.send_message(
                    chat_id,
                    "❌ **an error occurred**\n\n» **Clearing** __Queues__ **and leaving video chat.**",
                )
            else:
                # res expected to be [title, link, type]
                try:
                    title, link, mtype = res
                    await bot.send_message(
                        chat_id,
                        f"💡 **Streaming next track**\n\n🏷 **Name:** [{title}]({link}) | `{mtype}`\n💭 **Chat:** `{chat_id}`",
                        disable_web_page_preview=True,
                        reply_markup=keyboard,
                    )
                except Exception:
                    # in case res shape unexpected
                    logger.warning("Unexpected skip result: %s", res)
        else:
            # ignore other event types for now
            pass
    except Exception:
        logger.exception("Error in stream_end handler.")


# ---------------- utility ----------------


async def bash(cmd: str) -> Tuple[str, str]:
    """
    Run a shell command asynchronously and return (stdout, stderr).
    """
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    out = stdout.decode().strip()
    err = stderr.decode().strip()
    return out, err
