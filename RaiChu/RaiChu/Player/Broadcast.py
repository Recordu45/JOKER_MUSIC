# RaiChu/Player/Broadcast.py
import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatWriteForbidden, PeerIdInvalid, UserDeactivatedBan, RPCError

from Process.main import bot as Ufo   # your bot client
from RaiChu.config import SUDO_USERS

log = logging.getLogger(__name__)

# Usage: reply to a message with /gcast
@Ufo.on_message(filters.command("gcast") & filters.private)
async def broadcast(_, message: Message):
    # basic permission check
    try:
        sender_id = message.from_user.id
    except Exception:
        return await message.reply_text("Could not determine user. Aborting.")

    if sender_id not in SUDO_USERS:
        return await message.reply_text("🚫 You are not authorized to use this command.")

    # must reply to a message to broadcast
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message with /gcast to broadcast it.")

    text_to_send = message.reply_to_message.text or message.reply_to_message.caption or ""
    media = None
    # if original message had media, forward instead of send to preserve content
    if message.reply_to_message.media:
        media = message.reply_to_message

    status = await message.reply_text("🔁 Starting broadcast... Scanning dialogs.")
    sent = 0
    failed = 0
    total = 0

    # iterate dialogs (dialogs include users, groups, channels)
    async for dialog in Ufo.iter_dialogs():
        total += 1
        chat_id = dialog.chat.id

        # skip bots and broadcast to channels where bot has no permission
        try:
            # skip if it's a service/chat you shouldn't message
            if dialog.chat.is_bot:
                log.debug("Skipping bot chat %s", chat_id)
                continue
        except Exception:
            pass

        # polite short delay to reduce flood risk
        await asyncio.sleep(0.7)

        try:
            if media:
                # forward preserves media and caption
                await Ufo.forward_messages(chat_id, message.chat.id, message.reply_to_message.message_id)
            else:
                # send text; disable preview to reduce size
                await Ufo.send_message(chat_id, text_to_send, disable_web_page_preview=True)
            sent += 1
            # update progress occasionally (not every loop)
            if sent % 10 == 0:
                await status.edit(f"🔁 Broadcasting... Sent: {sent}  Failed: {failed}  Scanned: {total}")
        except FloodWait as e:
            wait = int(e.x) if hasattr(e, "x") else 10
            log.warning("FloodWait %s seconds, sleeping...", wait)
            await status.edit(f"⚠ FloodWait {wait}s — sleeping...")
            await asyncio.sleep(wait + 1)
            # after wait, retry sending once
            try:
                if media:
                    await Ufo.forward_messages(chat_id, message.chat.id, message.reply_to_message.message_id)
                else:
                    await Ufo.send_message(chat_id, text_to_send, disable_web_page_preview=True)
                sent += 1
            except Exception:
                failed += 1
        except (ChatWriteForbidden, PeerIdInvalid, UserDeactivatedBan, RPCError) as e:
            log.exception("Failed to send to %s: %s", chat_id, e)
            failed += 1
        except Exception as e:
            log.exception("Unexpected error while sending to %s: %s", chat_id, e)
            failed += 1

    # final status
    await status.edit(f"✅ Broadcast finished.\n\nTotal scanned: {total}\nSent: {sent}\nFailed: {failed}")
    await message.reply_text(f"✅ Gcast finished. Sent: {sent}, Failed: {failed}")
