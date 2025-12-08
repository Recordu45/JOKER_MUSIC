# RaiChu/Player/userbotjoin.py

import asyncio
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, FloodWait
from Process.filters import command
from Process.decorators import authorized_users_only, sudo_users_only, errors
from Process.main import aman as USER   # correct import
from RaiChu.config import BOT_USERNAME, SUDO_USERS


@Client.on_message(
    command(["userbotjoin", f"userbotjoin@{BOT_USERNAME}"])
    & filters.group
    & ~filters.edited
)
@authorized_users_only
@errors
async def userbot_join_group(bot, message):
    chat_id = message.chat.id

    # Step 1: check if bot has invite permission
    try:
        invite = await bot.export_chat_invite_link(chat_id)
    except Exception:
        return await message.reply(
            "❌ Bot needs **Add Users** permission to invite the assistant.\n"
            "Give permission and try again."
        )

    # Step 2: check assistant account
    try:
        assistant = await USER.get_me()
    except Exception:
        return await message.reply("❌ Assistant client is not connected.")

    # Step 3: try to join using invite link
    try:
        await USER.join_chat(invite)
    except UserAlreadyParticipant:
        pass
    except FloodWait as e:
        return await message.reply(
            f"⏳ FloodWait detected: Wait `{e.value}` seconds and try again."
        )
    except Exception as e:
        return await message.reply(
            "🛑 Assistant couldn't join your group.\n\n"
            f"**Reason:** `{e}`\n\n"
            "👉 You can also add the assistant manually."
        )

    return await message.reply("🤖 **Assistant joined the chat successfully.**")


# ---------------- LEAVE SINGLE GROUP ---------------- #

@Client.on_message(
    command(["userbotleave", f"leave@{BOT_USERNAME}"])
    & filters.group
    & ~filters.edited
)
@authorized_users_only
async def userbot_leave_group(bot, message):
    chat_id = message.chat.id

    try:
        await USER.send_message(chat_id, "👋 Assistant leaving chat.")
        await USER.leave_chat(chat_id)
    except Exception:
        return await message.reply(
            "❌ Assistant couldn't leave the chat. Possible FloodWait.\n"
            "Kick the assistant manually if needed."
        )

    await message.reply("✅ Assistant left the chat successfully.")


# ---------------- LEAVE ALL GROUPS ---------------- #

@Client.on_message(command(["leaveall", f"leaveall@{BOT_USERNAME}"]))
@sudo_users_only
async def leave_all_groups(bot, message):

    left = 0
    failed = 0
    status_msg = await message.reply("🔄 Leaving all groups...")

    async for dialog in USER.iter_dialogs():
        try:
            await USER.leave_chat(dialog.chat.id)
            left += 1
        except Exception:
            failed += 1

        await status_msg.edit(
            f"🚪 Leaving groups...\n\n"
            f"**Left:** {left}\n"
            f"**Failed:** {failed}"
        )

        await asyncio.sleep(0.7)

    await message.reply(
        f"🏁 **Finished**\n\n"
        f"✔ Left: `{left}` chats\n"
        f"❌ Failed: `{failed}` chats"
    )
