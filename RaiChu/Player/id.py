# RaiChu/Player/id.py
from Process.main import bot
from pyrogram import filters
from pyrogram.types import Message

@bot.on_message(filters.command("id") & ~filters.edited)
async def ids(_, message: Message):
    """Send IDs: user, replied user (if any) and chat id."""
    try:
        user = message.from_user
        if user is None:
            return await message.reply_text("Cannot determine your user info.")

        chat_id = message.chat.id

        reply = message.reply_to_message
        if reply and reply.from_user:
            replied_user = reply.from_user
            text = (
                f"**Your ID**: `{user.id}`\n"
                f"**{replied_user.first_name}'s ID**: `{replied_user.id}`\n"
                f"**Chat ID**: `{chat_id}`"
            )
            await message.reply_text(text)
        else:
            text = f"**Your ID**: `{user.id}`\n**Chat ID**: `{chat_id}`"
            await message.reply_text(text)
    except Exception as e:
        # safe fallback so handler never crashes the bot
        await message.reply_text(f"An error occurred: `{e}`")
