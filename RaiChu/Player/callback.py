# RaiChu/Player/callback.py
import re
import os
import yt_dlp
import logging
from typing import Optional

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaVideo,
)
from Process.main import bot
from Process.queues import QUEUE
from RaiChu.config import (
    ASSISTANT_NAME,
    BOT_NAME,
    BOT_USERNAME,
    GROUP_SUPPORT,
    OWNER_NAME,
    UPDATES_CHANNEL,
)
# optional markup helpers from your repo
try:
    from RaiChu.inline import (
        menu_markup,
        song_download_markup,
        stream_markup,
        audio_markup,
    )
except Exception:
    menu_markup = lambda user_id, *a, **k: [[InlineKeyboardButton("🔙 Back", callback_data="cbstart")]]
    song_download_markup = lambda vid: [[InlineKeyboardButton("🔙 Back", callback_data=f"song_back {vid}|0")]]
    stream_markup = lambda uid, *a, **k: [[InlineKeyboardButton("🔙 Back", callback_data="cbstart")]]
    audio_markup = lambda *a, **k: [[InlineKeyboardButton("🔙 Back", callback_data="cbstart")]]

log = logging.getLogger(__name__)


# ---------- simple start menu ----------
@bot.on_callback_query(filters.regex(r"cbstart"))
async def cbstart(_, query: CallbackQuery):
    await query.answer()
    text = (
        f"Hello, My name is {BOT_NAME}.\n\n"
        "I'm a Telegram streaming bot with several useful features.\n\n"
        "Feel free to add me to your groups."
    )
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Commands & Help ❔", callback_data="cbbasic")],
            [InlineKeyboardButton("How to Use Me ❓", callback_data="cbhowtouse")],
            [
                InlineKeyboardButton("Updates", url=f"https://t.me/{UPDATES_CHANNEL}"),
                InlineKeyboardButton("Support", url=f"https://t.me/{GROUP_SUPPORT}"),
            ],
            [
                InlineKeyboardButton(
                    "➕ Add Me To Your Group ➕",
                    url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
                )
            ],
        ]
    )
    try:
        await query.edit_message_text(text, reply_markup=markup, disable_web_page_preview=True)
    except Exception:
        # message may have been deleted or too old, just ignore
        pass


# ---------- how to use ----------
@bot.on_callback_query(filters.regex(r"cbhowtouse"))
async def cbguides(_, query: CallbackQuery):
    await query.answer()
    text = (
        "❓ Basic Guide for using this bot:\n\n"
        "1) Add me to your group.\n"
        "2) Promote me as administrator and give all permissions (avoid Anonymous Admin).\n"
        "3) Use /reload in the group to refresh admin data.\n"
        f"4) Add @{ASSISTANT_NAME} (userbot) to your group or use /userbotjoin.\n"
        "5) Start the video chat before playing music/video.\n\n"
        "If the userbot didn't join, try /userbotleave then /userbotjoin again."
    )
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="cbstart")]])
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except Exception:
        pass


# ---------- basic commands list ----------
@bot.on_callback_query(filters.regex(r"cbbasic"))
async def cbbasic(_, query: CallbackQuery):
    await query.answer()
    text = (
        "ℹ️ Command Menu\n\n"
        "• /id - Get your user id\n"
        "• /tm - Telegraph image link\n"
        "• /q - Convert reply to sticker\n"
        "• /speedtest - Speedtest\n"
        "• /play - Play by title or YouTube link\n"
        "• /vplay - Play video by title or link\n"
        "• /vstream - Play live stream or m3u8\n"
        "• /skip - Skip current song\n"
        "• /repo - Repo link\n"
        "• /end - End play"
    )
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Go Back", callback_data="cbstart")]])
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except Exception:
        pass


# ---------- control panel menu ----------
@bot.on_callback_query(filters.regex(r"cbmenu"))
async def cbmenu(_, query: CallbackQuery):
    await query.answer()
    try:
        member = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(member, "can_manage_voice_chats", False):
            return await query.answer(
                "Only admins with manage voice chats permission can tap this button.", show_alert=True
            )
    except Exception:
        return await query.answer("Could not verify permissions.", show_alert=True)

    chat_id = query.message.chat.id
    user_id = query.from_user.id
    buttons = menu_markup(user_id)
    if chat_id in QUEUE:
        await query.answer("Control Panel Opened")
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
        except Exception:
            pass
    else:
        await query.answer("❌ Nothing is Currently Streaming", show_alert=True)


# ---------- download menu (callback) ----------
@bot.on_callback_query(filters.regex(r"cbdown"))
async def cbdown(_, query: CallbackQuery):
    await query.answer()
    data = query.data or ""
    # format: "cbdown <videoid>|<user>"
    parts = data.split(None, 1)
    if len(parts) < 2:
        return await query.answer("Invalid callback data.", show_alert=True)
    callback_request = parts[1]
    # some handlers expect "videoid|user"
    try:
        videoid, user_id = callback_request.split("|")
    except ValueError:
        videoid = callback_request
        user_id = str(query.from_user.id)
    buttons = song_download_markup(videoid)
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        pass


# ---------- song back helper (show formats again) ----------
@bot.on_callback_query(filters.regex(r"song_back"))
async def songs_back_helper(_, query: CallbackQuery):
    await query.answer()
    data = query.data or ""
    parts = data.split(None, 1)
    if len(parts) < 2:
        return await query.answer("Invalid callback data.", show_alert=True)
    callback_request = parts[1]
    try:
        stype, videoid = callback_request.split("|")
    except ValueError:
        # fallback if only videoid present
        videoid = callback_request.split("|")[-1]
    buttons = song_download_markup(videoid)
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        pass


# ---------- song formats & download helper (guarded) ----------
@bot.on_callback_query(filters.regex(r"gets"))
async def song_helper_cb(_, query: CallbackQuery):
    await query.answer()
    data = query.data or ""
    parts = data.split(None, 1)
    if len(parts) < 2:
        return await query.answer("Invalid callback data.", show_alert=True)
    callback_request = parts[1]
    # expected pattern: "<stype>|<videoid>"
    try:
        stype, videoid = callback_request.split("|")
    except ValueError:
        return await query.answer("Invalid parameters.", show_alert=True)

    # If your repo supplies a YouTube helper, use it. Otherwise show message.
    try:
        YouTube = globals().get("YouTube", None)
        if YouTube and hasattr(YouTube, "formats"):
            formats_available, link = await YouTube.formats(videoid, True)
        else:
            # fallback: attempt to use yt_dlp to fetch formats (best-effort)
            with yt_dlp.YoutubeDL({"quiet": True}) as ytdl:
                info = ytdl.extract_info(f"https://www.youtube.com/watch?v={videoid}", download=False)
            formats_available = info.get("formats", [])
            link = info.get("webpage_url", None)
    except Exception as e:
        log.exception("formats fetch error: %s", e)
        return await query.edit_message_text("Could not fetch formats for this video.")

    # Build a simple keyboard listing audio/video options (guarded)
    keyboard = []
    if stype == "audio":
        done = set()
        for fmt in formats_available:
            fformat = fmt.get("format", "")
            if "audio" not in fformat:
                continue
            fid = fmt.get("format_id")
            filesize = fmt.get("filesize") or fmt.get("filesize_approx")
            if filesize is None:
                continue
            label = fmt.get("format_note") or fmt.get("ext") or str(fid)
            if label in done:
                continue
            done.add(label)
            sz = f"{round((filesize or 0) / (1024*1024), 2)} MB"
            keyboard.append([InlineKeyboardButton(text=f"{label} — {sz}", callback_data=f"song_download audio|{fid}|{videoid}")])
    else:
        # video: select some common MP4 formats
        done = set()
        for fmt in formats_available:
            fid = fmt.get("format_id")
            filesize = fmt.get("filesize") or fmt.get("filesize_approx")
            if filesize is None:
                continue
            if int(fmt.get("height", 0)) < 240:
                continue
            label = f"{fmt.get('height', '')}p"
            if label in done:
                continue
            done.add(label)
            sz = f"{round((filesize or 0) / (1024*1024), 2)} MB"
            keyboard.append([InlineKeyboardButton(text=f"{label} — {sz}", callback_data=f"song_download video|{fid}|{videoid}")])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"song_back {stype}|{videoid}"),
                     InlineKeyboardButton("✖️ Close", callback_data="cls")])
    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        pass


# ---------- song download & send (heavier; guarded) ----------
@bot.on_callback_query(filters.regex(r"song_download"))
async def song_download_cb(_, query: CallbackQuery):
    await query.answer()
    data = query.data or ""
    parts = data.split(None, 1)
    if len(parts) < 2:
        return await query.answer("Invalid callback data.", show_alert=True)
    callback_request = parts[1]
    # expected: "<stype>|<format_id>|<videoid>"
    try:
        stype, format_id, videoid = callback_request.split("|")
    except ValueError:
        return await query.answer("Invalid parameters.", show_alert=True)

    # Busy indicator
    try:
        await query.edit_message_text("🔄 Preparing your download...")
    except Exception:
        pass

    # Try to use a YouTube helper if present in the repo
    YouTube = globals().get("YouTube", None)
    if YouTube and hasattr(YouTube, "download"):
        try:
            # This is repo-specific API; call it if available
            filename = await YouTube.download(
                f"https://www.youtube.com/watch?v={videoid}",
                query,
                songaudio=(stype == "audio"),
                songvideo=(stype == "video"),
                format_id=format_id,
            )
            if not filename:
                return await query.edit_message_text("Failed to download.")
            # send file
            if stype == "video":
                await query.message.reply_video(filename)
            else:
                await query.message.reply_audio(filename)
            # cleanup
            try:
                os.remove(filename)
            except:
                pass
            return await query.edit_message_text("✅ Download sent.")
        except Exception as e:
            log.exception("YouTube.download error: %s", e)
            return await query.edit_message_text("Failed to download via helper.")
    else:
        # fallback: attempt direct yt_dlp download (simple)
        tmp_name = f"/tmp/{videoid}_{format_id}.{ 'mp4' if stype=='video' else 'mp3'}"
        ydl_opts = {"quiet": True, "outtmpl": tmp_name}
        if stype == "audio":
            ydl_opts.update({"format": f"{format_id}/bestaudio", "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]})
        else:
            ydl_opts.update({"format": f"{format_id}/best"})
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ytdl:
                ytdl.extract_info(f"https://www.youtube.com/watch?v={videoid}", download=True)
            # send file
            if stype == "video":
                await query.message.reply_video(tmp_name)
            else:
                await query.message.reply_audio(tmp_name)
            try:
                os.remove(tmp_name)
            except:
                pass
            return await query.edit_message_text("✅ Downloaded and sent.")
        except Exception as e:
            log.exception("yt_dlp download error: %s", e)
            try:
                await query.edit_message_text("Failed to download media.")
            except:
                pass
            return


# ---------- home/control (stream) ----------
@bot.on_callback_query(filters.regex(r"cbhome"))
async def cbhome(_, query: CallbackQuery):
    await query.answer()
    try:
        member = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(member, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can tap.", show_alert=True)
    except Exception:
        return await query.answer("Permission check failed.", show_alert=True)

    chat_id = query.message.chat.id
    user_id = query.from_user.id
    # dlurl may be undefined; guard it
    dlurl = globals().get("dlurl", "")
    try:
        buttons = stream_markup(user_id, dlurl)
    except Exception:
        buttons = menu_markup(user_id)
    if chat_id in QUEUE:
        await query.answer("Back")
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
        except:
            pass
    else:
        await query.answer("❌ Nothing is currently streaming", show_alert=True)


# ---------- close message ----------
@bot.on_callback_query(filters.regex(r"cls"))
async def close(_, query: CallbackQuery):
    await query.answer()
    try:
        member = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(member, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
    except Exception:
        # still attempt to delete
        pass
    try:
        await query.message.delete()
    except Exception:
        try:
            await query.answer("Could not delete message.", show_alert=True)
        except:
            pass
