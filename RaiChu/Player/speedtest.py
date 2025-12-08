# RaiChu/Player/speedtest.py

import os
import asyncio
import speedtest
import aiohttp
from PIL import Image
from pyrogram import filters
from pyrogram.types import Message

from Process.main import bot as app
from RaiChu.config import SUDO_USERS as SUDOERS


# ---------- Async file downloader ----------
async def download_file(url: str, path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            with open(path, "wb") as f:
                f.write(data)
    return path


# ---------- Threaded speedtest execution ----------
async def run_speedtest_in_thread():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, run_speedtest_sync)


def run_speedtest_sync():
    test = speedtest.Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    return test.results.dict()


# ---------- MAIN HANDLER ----------
@app.on_message(filters.command("speedtest") & ~filters.edited)
async def speedtest_handler(_, message: Message):
    user = message.from_user.id
    if user not in SUDOERS:
        return await message.reply("❌ Only sudo users can use this command.")

    m = await message.reply("⚙️ Running Speedtest… (takes 5–15 seconds)")

    # Run speedtest without freezing bot
    try:
        results = await run_speedtest_in_thread()
    except Exception as e:
        return await m.edit(f"❌ Error running speedtest:\n`{e}`")

    share_url = results.get("share")
    img_path = None

    # ---------- Download share image (optional) ----------
    if share_url:
        img_path = "/tmp/speedtest.png"
        try:
            await download_file(share_url, img_path)
            # Crop safely
            try:
                img = Image.open(img_path)
                # crop protection
                w, h = img.size
                crop_box = (10, 10, w - 10, h - 10)
                cropped = img.crop(crop_box)
                cropped.save(img_path)
            except:
                pass
        except:
            img_path = None

    output = f"""💠 **Speedtest Results**
    
<b>Client:</b>
• ISP: {results['client']['isp']}
• Country: {results['client']['country']}

<b>Server:</b>
• Name: {results['server']['name']}
• Country: {results['server']['country']}
• Sponsor: {results['server']['sponsor']}
• Latency: {results['server']['latency']}

⚡ **Ping:** {results['ping']}
"""

    # ---------- Send output ----------
    if img_path and os.path.exists(img_path):
        await app.send_photo(message.chat.id, photo=img_path, caption=output)
        os.remove(img_path)
        await m.delete()
    else:
        await m.edit(output)
