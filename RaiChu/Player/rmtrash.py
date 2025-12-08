# RaiChu/Player/rmtrash.py

import os
from pyrogram.types import Message
from Process.main import bot
from Process.filters import command
from Process.decorators import sudo_users_only

DOWNLOAD_DIR = os.path.realpath("RaiChu/downloads")
RAW_DIR = os.path.realpath("RaiChu/raw")  # safer separate folder

# Ensure folders exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)


# ---------------- CLEAR DOWNLOADS ----------------
@bot.on_message(command(["rmd", "clear"]) & ~bot.filters.edited)
@sudo_users_only
async def clear_downloads(_, message: Message):
    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        return await message.reply_text("❌ No downloaded files found.")

    deleted = 0
    for f in files:
        try:
            os.remove(os.path.join(DOWNLOAD_DIR, f))
            deleted += 1
        except:
            pass

    await message.reply_text(f"✅ Deleted {deleted} downloaded files.")


# ---------------- CLEAR RAW FILES ----------------
@bot.on_message(command(["rmw", "clean"]) & ~bot.filters.edited)
@sudo_users_only
async def clear_raw(_, message: Message):
    files = os.listdir(RAW_DIR)
    deleted = 0

    for f in files:
        if f.endswith(".raw"):
            try:
                os.remove(os.path.join(RAW_DIR, f))
                deleted += 1
            except:
                pass

    if deleted:
        await message.reply_text(f"✅ Deleted {deleted} raw files.")
    else:
        await message.reply_text("❌ No raw files found.")


# ---------------- SAFE CLEANUP ----------------
@bot.on_message(command(["cleanup"]) & ~bot.filters.edited)
@sudo_users_only
async def cleanup(_, message: Message):
    """
    Cleanup ONLY inside RaiChu/raw and RaiChu/downloads.
    Prevents entire repo deletion on Render.
    """
    deleted = 0

    # Clean raw files
    for f in os.listdir(RAW_DIR):
        if f.endswith((".raw", ".jpg", ".jpeg", ".png")):
            try:
                os.remove(os.path.join(RAW_DIR, f))
                deleted += 1
            except:
                pass

    # Clean downloads
    for f in os.listdir(DOWNLOAD_DIR):
        try:
            os.remove(os.path.join(DOWNLOAD_DIR, f))
            deleted += 1
        except:
            pass

    if deleted:
        await message.reply_text(f"🧹 Cleaned {deleted} temporary files.")
    else:
        await message.reply_text("✔ Already clean.")
