# RaiChu/Player/song.py
from __future__ import unicode_literals

import os
import asyncio
import aiofiles
import aiohttp
import yt_dlp
from pyrogram import filters
from pyrogram.types import Message

from Process.main import bot
from RaiChu.config import BOT_USERNAME as BN
from Process.filters import command

TMP_DIR = "/tmp/raichu_songs"
os.makedirs(TMP_DIR, exist_ok=True)


# ---------------- YT SEARCH (safe) ----------------
async def yt_search(query: str):
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": "in_playlist",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if not info or not info.get("entries"):
                return None
            entry = info["entries"][0]
            return {
                "title": entry.get("title"),
                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                "duration": entry.get("duration") or 0,
                "thumbnail": entry.get("thumbnail"),
            }
    except Exception:
        return None


# ---------------- FILE DOWNLOAD ----------------
async def download_from_url(url: str, filename: str):
    try:
        path = os.path.join(TMP_DIR, filename)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    return None
                f = await aiofiles.open(path, "wb")
                await f.write(await r.read())
                await f.close()
        return path
    except:
        return None


# ---------------- /song handler ----------------
@bot.on_message(command(["song", f"song@{BN}"]) & ~filters.edited)
async def song_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("🎵 Please give a song name.")

    query = " ".join(m.command[1:])
    status = await m.reply("🔎 Searching song…")

    data = await yt_search(query)
    if not data:
        return await status.edit("❌ Song not found.")

    title = data["title"]
    url = data["url"]
    thumbnail = data["thumbnail"]
    duration = data["duration"]

    await status.edit("📥 Downloading audio…")

    # download best audio
    audio_path = os.path.join(TMP_DIR, f"{title}.m4a")

    try:
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": audio_path,
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return await status.edit(f"❌ Error downloading audio\n`{e}`")

    # thumbnail
    thumb_path = None
    if thumbnail:
        thumb_path = await download_from_url(thumbnail, f"{title}.jpg")

    await status.edit("📤 Uploading…")

    try:
        await m.reply_audio(
            audio_path,
            caption=f"🎧 {title}",
            title=title,
            duration=duration,
            thumb=thumb_path if thumb_path else None,
        )
    except Exception as e:
        await status.edit(f"❌ Upload failed\n`{e}`")
    else:
        await status.delete()

    # cleanup
    try:
        os.remove(audio_path)
        if thumb_path:
            os.remove(thumb_path)
    except:
        pass


# ---------------- /vsong handler ----------------
@bot.on_message(command(["vsong", f"vsong@{BN}", "video", f"video@{BN}"]) & ~filters.edited)
async def vsong_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("🎬 Give a video name to search.")

    query = " ".join(m.command[1:])
    status = await m.reply("🔎 Searching video…")

    data = await yt_search(query)
    if not data:
        return await status.edit("❌ Video not found.")

    title = data["title"]
    url = data["url"]
    thumbnail = data["thumbnail"]
    duration = data["duration"]

    await status.edit("📥 Downloading video…")

    video_path = os.path.join(TMP_DIR, f"{title}.mp4")
    thumb_path = None

    try:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": video_path,
            "merge_output_format": "mp4",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return await status.edit(f"❌ Error downloading video\n`{e}`")

    if thumbnail:
        thumb_path = await download_from_url(thumbnail, f"{title}.jpg")

    await status.edit("📤 Uploading…")

    try:
        await m.reply_video(
            video_path,
            caption=f"🎬 {title}",
            duration=duration,
            thumb=thumb_path if thumb_path else None,
        )
    except Exception as e:
        await status.edit(f"❌ Upload failed\n`{e}`")
    else:
        await status.delete()

    # cleanup
    try:
        os.remove(video_path)
        if thumb_path:
            os.remove(thumb_path)
    except:
        pass


# ---------------- /lyric handler (fixed API) ----------------
@bot.on_message(command(["lyric", f"lyric@{BN}"]) & ~filters.edited)
async def lyric_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("🎼 Give a song name for lyrics.")

    query = " ".join(m.command[1:])
    status = await m.reply("🔎 Searching lyrics…")

    try:
        # working lyrics API
        url = f"https://some-random-api.com/lyrics?title={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                data = await r.json()

        lyrics = data.get("lyrics")
        if not lyrics:
            return await status.edit("❌ Lyrics not found.")

        title = data.get("title", query)
        return await status.edit(f"🎼 **{title}**\n\n{lyrics[:3800]}")

    except Exception:
        return await status.edit("❌ Could not fetch lyrics.")
