# RaiChu/Player/telegraph.py

import os
from pyrogram import filters
from telegraph import upload_file
from Process.main import bot as app


DOWNLOAD_DIR = "root/downloads"


# Create directory if missing
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@app.on_message(filters.command(["telegraph", "tm", "tgm"]))
async def telegraph_handler(client, message):
    replied = message.reply_to_message

    if not replied:
        return await message.reply("Reply to an image, gif, short mp4 or document under 5MB.")

    # ---------- Validate File ----------
    file_ok = False
    five_mb = 5 * 1024 * 1024

    if replied.photo and replied.photo.file_size <= five_mb:
        file_ok = True

    elif (
        replied.animation
        and replied.animation.file_size <= five_mb
    ):
        file_ok = True

    elif (
        replied.video
        and replied.video.file_name.endswith(".mp4")
        and replied.video.file_size <= five_mb
    ):
        file_ok = True

    elif (
        replied.document
        and replied.document.file_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".mp4")
        )
        and replied.document.file_size <= five_mb
    ):
        file_ok = True

    if not file_ok:
        return await message.reply("❌ Unsupported or too large file (max 5MB).")

    # ---------- Download ----------
    try:
        download_location = await client.download_media(
            message=replied,
            file_name=f"{DOWNLOAD_DIR}/",
        )
    except Exception as e:
        return await message.reply(f"Download failed:\n`{e}`")

    # ---------- Upload to Telegraph ----------
    try:
        response = upload_file(download_location)
        url = f"https://telegra.ph{response[0]}"
    except Exception as e:
        await message.reply(f"Upload failed:\n`{e}`")
        url = None

    # ---------- Clean Up ----------
    try:
        os.remove(download_location)
    except:
        pass

    # ---------- Send result ----------
    if url:
        await message.reply(
            f"🔗 **Uploaded Successfully!**\n\n👉 {url}",
            disable_web_page_preview=True,
        )
