# RaiChu/Player/play.py
import asyncio
import os
import re
import logging
from typing import Optional

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant

from Process.main import bot, call_py, aman as user  # ensure Process.main exports these
from Process.filters import command, other_filters
from Process.queues import QUEUE, add_to_queue
from Process.utils import bash  # optional helper you had
from RaiChu.inline import stream_markup, audio_markup
from RaiChu.config import ASSISTANT_NAME, BOT_USERNAME, IMG_1, IMG_2, IMG_5

from pytgcalls.types.input_stream import AudioPiped
from pytgcalls import StreamType

# small logger
log = logging.getLogger(__name__)

# ---------- helper: yt-dlp to get playable stream url ----------
async def get_stream_url(url: str, max_width: int = 1280, max_height: int = 720, timeout: int = 25) -> Optional[str]:
    """
    Use yt-dlp to fetch a direct stream URL that works with AudioPiped.
    Returns direct url string or None on failure.
    """
    # prefer yt-dlp CLI with -g to get best matching format
    cmd = f'yt-dlp -g -f "(bv*[height<={max_height}]+ba/bestaudio)" "{url}"'
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return None
        out = (stdout or b"").decode().strip()
        if not out:
            return None
        # take first non-empty line
        for line in out.splitlines():
            line = line.strip()
            if line:
                return line
    except Exception as e:
        log.exception("get_stream_url error: %s", e)
        return None
    return None


# ---------- ytsearch helper (simple) ----------
def ytsearch(query: str):
    try:
        from youtubesearchpython import VideosSearch
        search = VideosSearch(query, limit=1).result()
        if not search or not search.get("result"):
            return None
        data = search["result"][0]
        return {
            "title": data.get("title"),
            "url": data.get("link"),
            "duration": data.get("duration", "0:00"),
            "thumbnail": f"https://i.ytimg.com/vi/{data.get('id')}/hqdefault.jpg",
            "videoid": data.get("id"),
        }
    except Exception as e:
        log.exception("ytsearch error: %s", e)
        return None


# ---------- main handler ----------
@bot.on_message(command(["play", f"play@{BOT_USERNAME}"]) & other_filters)
async def play(_, m: Message):
    # delete user command for cleanliness where you intended
    try:
        await m.delete()
    except:
        pass

    chat_id = m.chat.id
    user_id = m.from_user.id

    # buttons for replies (audio UI)
    try:
        buttons = audio_markup(user_id)
    except Exception:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("• Close", callback_data="cls")]])

    # anonymous admin check
    if m.sender_chat:
        return await m.reply_text("You're an Anonymous Admin. Revert to user account to use this command.")

    # check bot permissions in group
    try:
        me = await _.get_me()
        bot_member = await _.get_chat_member(chat_id, me.id)
    except Exception as e:
        return await m.reply_text(f"Error fetching bot info: `{e}`")

    if getattr(bot_member, "status", "") != "administrator":
        return await m.reply_text(
            "I need to be an Administrator with these permissions:\n"
            "• Manage video chats\n• Add users\n• Delete messages"
        )

    if not getattr(bot_member, "can_manage_voice_chats", False):
        return await m.reply_text("Missing permission: Manage video chats")

    # ensure assistant/userbot is in group (join if necessary)
    try:
        ubot_id = (await user.get_me()).id
        ubot_member = await _.get_chat_member(chat_id, ubot_id)
        if getattr(ubot_member, "status", "") == "kicked":
            return await m.reply_text(f"Assistant @{ASSISTANT_NAME} is banned in this group. Unban first.")
    except UserNotParticipant:
        # try to join via username or invite link
        try:
            if m.chat.username:
                await user.join_chat(f"@{m.chat.username}")
            else:
                inv = await _.export_chat_invite_link(chat_id)
                await user.join_chat(inv)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            return await m.reply_text(f"Userbot failed to join: `{e}`")
    except Exception:
        # ignore other errors while checking membership
        pass

    # If user replied to an audio/voice: download and play that
    replied = m.reply_to_message
    if replied and (replied.audio or replied.voice):
        msg = await m.reply_text("📥 Downloading audio...")
        # download to a temp file
        try:
            dl_path = await replied.download()
        except Exception as e:
            await msg.delete()
            return await m.reply_text(f"Download failed: `{e}`")
        # If queue exists, add to queue
        songname = getattr(replied.audio, "title", None) or getattr(replied.audio, "file_name", None) or "Audio"
        link = getattr(replied, "link", "")
        if chat_id in QUEUE:
            pos = add_to_queue(chat_id, songname, dl_path, link, "Audio", 0)
            await msg.delete()
            return await m.reply_photo(
                photo=IMG_1,
                caption=f"Track added to queue » `{pos}`\nName: {songname}\nChat: `{chat_id}`\nRequested by: {m.from_user.mention()}",
                reply_markup=buttons,
            )
        # no queue: join and play local file
        try:
            await call_py.join_group_call(
                chat_id,
                AudioPiped(dl_path),
                stream_type=StreamType().local_stream,
            )
            add_to_queue(chat_id, songname, dl_path, link, "Audio", 0)
            await msg.delete()
            return await m.reply_photo(
                photo=IMG_2,
                caption=f"Now playing: {songname}\nRequested by: {m.from_user.mention()}",
                reply_markup=buttons,
            )
        except Exception as e:
            await msg.delete()
            return await m.reply_text(f"Failed to play audio: `{e}`")

    # else: use text argument or show usage
    if len(m.command) < 2:
        return await m.reply_photo(
            photo=IMG_5,
            caption="Usage: /play <song name or YouTube link>\nOr reply to an audio message with /play",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("• Support", url=f"https://t.me/{GROUP_SUPPORT}"), InlineKeyboardButton("• Close", callback_data="cls")]]
            ),
        )

    query = m.text.split(None, 1)[1].strip()
    # if query looks like a YouTube link, use it, else search
    is_url = query.startswith("http://") or query.startswith("https://")
    info = None
    if not is_url:
        info = ytsearch(query)
        if not info:
            return await m.reply_text("No results found for your query.")
        url = info["url"]
        title = info["title"][:80]
        # optional thumbnail/videoid
        videoid = info.get("videoid")
    else:
        url = query
        title = url

    status = await m.reply_text(f"🔎 Preparing: `{title}`\nPlease wait...")
    # get playable direct link
    stream_url = await get_stream_url(url)
    if not stream_url:
        await status.edit("⚠ Failed to extract a playable stream URL.")
        return

    # if queue present: add and notify
    if chat_id in QUEUE:
        pos = add_to_queue(chat_id, title, stream_url, url, "Audio", 0)
        await status.delete()
        return await m.reply_photo(
            photo=IMG_1,
            caption=f"Added to queue » `{pos}`\nName: {title}\nRequested by: {m.from_user.mention()}",
            reply_markup=buttons,
        )

    # else join and play
    try:
        await call_py.join_group_call(
            chat_id,
            AudioPiped(stream_url),
            stream_type=StreamType().local_stream,
        )
        add_to_queue(chat_id, title, stream_url, url, "Audio", 0)
        await status.delete()
        keyboard = stream_markup(user_id, url) if callable(stream_markup) else buttons
        return await m.reply_photo(
            photo=IMG_2,
            caption=f"▶ Now streaming: {title}\nRequested by: {m.from_user.mention()}",
            reply_markup=keyboard,
        )
    except Exception as e:
        await status.delete()
        return await m.reply_text(f"Failed to start stream: `{e}`")
