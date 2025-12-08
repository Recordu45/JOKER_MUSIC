# RaiChu/Player/Buger.py
"""Bug / Glitch Text Generator"""

import random
from pyrogram import filters
from pyrogram.types import Message

from Process.main import bot  # import your bot client

GLITCH_CHARS = [
    "̷", "̸", "͜", "͓̽", "̴", "͠", "̼", "̳", "̟", 
    "̘", "͍", "̦", "͓", "̤", "̞", "̺", "̫", "̱",
    "ͅ", "͔", "̰", "̙", "͚", "̥", "͓"
]

def make_bug(text: str) -> str:
    """Return corrupted bug-style text."""
    bugged = ""
    for ch in text:
        bugged += ch + random.choice(GLITCH_CHARS)
        if random.random() < 0.2:  # occasional extra glitching
            bugged += random.choice(GLITCH_CHARS)
    return bugged


@bot.on_message(filters.command("bug") & filters.reply)
async def bug_handler(_, message: Message):
    """Reply to a message with /bug to glitch it."""
    reply = message.reply_to_message

    if not reply.text:
        return await message.reply_text("Reply to a TEXT message only.")

    glitched = make_bug(reply.text)
    await message.reply_text(glitched)
