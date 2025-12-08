# RaiChu/Player/admins.py
import asyncio
import logging
from os import remove as os_remove
from typing import Optional

from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from Process.main import bot, call_py
from Process.Cache.admins import admins
from Process.decorators import authorized_users_only
from Process.filters import command, other_filters
from Process.queues import QUEUE, clear_queue
from Process.utils import skip_current_song, skip_item  # these should exist in repo
from RaiChu.config import (
    BOT_USERNAME,
    GROUP_SUPPORT,
    IMG_3,
    UPDATES_CHANNEL,
    IMG_5,
)

# Try to import optional helpers; if missing, provide safe fallbacks
try:
    from Process.utils import remove_if_exists, thumb, CHAT_TITLE
except Exception:
    remove_if_exists = lambda path: None  # noop

    async def thumb(thumbnail, title, userid, ctitle):
        # fallback: return thumbnail or placeholder string
        return thumbnail or ""

    async def CHAT_TITLE(name):
        return name or ""

log = logging.getLogger(__name__)

# small helper: call a function if exists and await if needed
async def _maybe_await(maybe_coro):
    if maybe_coro is None:
        return None
    if asyncio.iscoroutine(maybe_coro) or asyncio.iscoroutinefunction(maybe_coro):
        return await maybe_coro
    return maybe_coro

# Compatibility wrappers for PyTgCalls methods (older/newer method names)
async def leave_group_call_safe(chat_id: int):
    for name in ("leave_group_call", "leave_call"):
        fn = getattr(call_py, name, None)
        if fn:
            res = fn(chat_id)
            if asyncio.iscoroutine(res):
                await res
            return

async def pause_stream_safe(chat_id: int):
    for name in ("pause_stream", "pause"):
        fn = getattr(call_py, name, None)
        if fn:
            res = fn(chat_id)
            if asyncio.iscoroutine(res):
                await res
            return

async def resume_stream_safe(chat_id: int):
    for name in ("resume_stream", "resume"):
        fn = getattr(call_py, name, None)
        if fn:
            res = fn(chat_id)
            if asyncio.iscoroutine(res):
                await res
            return

async def mute_stream_safe(chat_id: int):
    for name in ("mute_stream", "mute"):
        fn = getattr(call_py, name, None)
        if fn:
            res = fn(chat_id)
            if asyncio.iscoroutine(res):
                await res
            return

async def unmute_stream_safe(chat_id: int):
    for name in ("unmute_stream", "unmute"):
        fn = getattr(call_py, name, None)
        if fn:
            res = fn(chat_id)
            if asyncio.iscoroutine(res):
                await res
            return

async def change_volume_safe(chat_id: int, volume: int):
    # volume function name differs: change_volume_call / change_volume
    for name in ("change_volume_call", "change_volume"):
        fn = getattr(call_py, name, None)
        if fn:
            res = fn(chat_id, volume)
            if asyncio.iscoroutine(res):
                await res
            return
    raise AttributeError("change_volume function not found on call_py")


# Inline keyboard small helpers
bttn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Go Back", callback_data="cbmenu")]])
bcl = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Close", callback_data="cls")]])


# ----------------------- reload admin list -----------------------
@bot.on_message(command(["reload", f"reload@{BOT_USERNAME}"]) & other_filters)
@authorized_users_only
async def update_admin(_, message: Message):
    try:
        new_admins = []
        async for m in bot.get_chat_members(message.chat.id, filter="administrators"):
            new_admins.append(m.user.id)
        admins[message.chat.id] = new_admins
        await message.reply_text(
            "✅ Bot reloaded correctly!\n✅ Admin list updated."
        )
    except Exception as e:
        log.exception("Failed reloading admins: %s", e)
        await message.reply_text(f"❌ Failed to reload admins: {e}")


# ----------------------- skip command -----------------------
@bot.on_message(command(["skip", f"skip@{BOT_USERNAME}", "vskip"]) & other_filters)
@authorized_users_only
async def skip(_, m: Message):
    chat_id = m.chat.id

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="• Menu", callback_data="cbmenu"),
                InlineKeyboardButton(text="• Close", callback_data="cls"),
            ]
        ]
    )

    try:
        if len(m.command) < 2:
            op = await skip_current_song(chat_id)
            # skip_current_song return patterns handled
            if op == 0:
                await m.reply("❌ Nothing is currently playing.")
            elif op == 1:
                await m.reply("✅ Queue is empty. Userbot leaving voice chat.")
            elif op == 2:
                await m.reply("🗑️ Clearing the Queue. Userbot leaving voice chat.")
            else:
                # op expected as (title, url) or similar
                try:
                    title, url = op[0], op[1]
                except Exception:
                    title, url = str(op), ""
                await m.reply_photo(
                    photo=f"{IMG_3}",
                    caption=f"⏭ Skipped to next track.\n\nName: [{title}]({url})\nChat: `{chat_id}`\nStatus: `Playing`\nRequest by: {m.from_user.mention()}",
                    reply_markup=keyboard,
                )
        else:
            # remove specific items from queue: /skip 2 3 5
            skip_arg = " ".join(m.command[1:])
            OP = "🗑 Removed from queue:"
            if chat_id in QUEUE:
                items = [int(x) for x in skip_arg.split() if x.isdigit()]
                items.sort(reverse=True)
                removed = []
                for x in items:
                    if x == 0:
                        continue
                    hm = await skip_item(chat_id, x)
                    if hm:
                        removed.append(f"#{x} - {hm}")
                if removed:
                    OP += "\n" + "\n".join(removed)
                await m.reply(OP)
            else:
                await m.reply("❌ No queue present for this chat.")
    except Exception as e:
        log.exception("Error in skip command: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


# ----------------------- stop command -----------------------
@bot.on_message(command(["stop", f"stop@{BOT_USERNAME}", "end", f"end@{BOT_USERNAME}", "vstop"]) & other_filters)
@authorized_users_only
async def stop(_, m: Message):
    chat_id = m.chat.id
    try:
        if chat_id in QUEUE:
            await leave_group_call_safe(chat_id)
            clear_queue(chat_id)
            await m.reply("✅ Userbot disconnected from the voice chat.")
        else:
            await m.reply("❌ Nothing is streaming.")
    except Exception as e:
        log.exception("Error stopping: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


# ----------------------- pause/resume/mute/unmute -----------------------
@bot.on_message(command(["pause", f"pause@{BOT_USERNAME}", "vpause"]) & other_filters)
@authorized_users_only
async def pause(_, m: Message):
    chat_id = m.chat.id
    try:
        if chat_id in QUEUE:
            await pause_stream_safe(chat_id)
            await m.reply("⏸ Track paused. Use /resume to continue.")
        else:
            await m.reply("❌ Nothing is streaming.")
    except Exception as e:
        log.exception("Pause error: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


@bot.on_message(command(["resume", f"resume@{BOT_USERNAME}", "vresume"]) & other_filters)
@authorized_users_only
async def resume(_, m: Message):
    chat_id = m.chat.id
    try:
        if chat_id in QUEUE:
            await resume_stream_safe(chat_id)
            await m.reply("▶️ Track resumed. Use /pause to pause.")
        else:
            await m.reply("❌ Nothing is streaming.")
    except Exception as e:
        log.exception("Resume error: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


@bot.on_message(command(["mute", f"mute@{BOT_USERNAME}", "vmute"]) & other_filters)
@authorized_users_only
async def mute(_, m: Message):
    chat_id = m.chat.id
    try:
        if chat_id in QUEUE:
            await mute_stream_safe(chat_id)
            await m.reply("🔇 Userbot muted. Use /unmute to unmute.")
        else:
            await m.reply("❌ Nothing is streaming.")
    except Exception as e:
        log.exception("Mute error: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


@bot.on_message(command(["unmute", f"unmute@{BOT_USERNAME}", "vunmute"]) & other_filters)
@authorized_users_only
async def unmute(_, m: Message):
    chat_id = m.chat.id
    try:
        if chat_id in QUEUE:
            await unmute_stream_safe(chat_id)
            await m.reply("🔊 Userbot unmuted. Use /mute to mute.")
        else:
            await m.reply("❌ Nothing is streaming.")
    except Exception as e:
        log.exception("Unmute error: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


# ----------------------- callback handlers -----------------------
@bot.on_callback_query(filters.regex("cbpause"))
async def cbpause(_, query: CallbackQuery):
    try:
        if query.message.sender_chat:
            return await query.answer("You're an Anonymous Admin. Revert to your user account.", show_alert=True)
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(a, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
        chat_id = query.message.chat.id
        if chat_id in QUEUE:
            await pause_stream_safe(chat_id)
            await query.edit_message_text("⏸ The streaming has paused", reply_markup=bttn)
        else:
            await query.answer("❌ Nothing is currently streaming", show_alert=True)
    except Exception as e:
        log.exception("cbpause error: %s", e)
        try:
            await query.edit_message_text(f"🚫 Error:\n`{e}`", reply_markup=bcl)
        except:
            await query.answer("An error occurred.", show_alert=True)


@bot.on_callback_query(filters.regex("cbresume"))
async def cbresume(_, query: CallbackQuery):
    try:
        if query.message.sender_chat:
            return await query.answer("You're an Anonymous Admin. Revert to your user account.", show_alert=True)
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(a, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
        chat_id = query.message.chat.id
        if chat_id in QUEUE:
            await resume_stream_safe(chat_id)
            await query.edit_message_text("▶️ The streaming has resumed", reply_markup=bttn)
        else:
            await query.answer("❌ Nothing is currently streaming", show_alert=True)
    except Exception as e:
        log.exception("cbresume error: %s", e)
        try:
            await query.edit_message_text(f"🚫 Error:\n`{e}`", reply_markup=bcl)
        except:
            await query.answer("An error occurred.", show_alert=True)


@bot.on_callback_query(filters.regex("cbstop"))
async def cbstop(_, query: CallbackQuery):
    try:
        if query.message.sender_chat:
            return await query.answer("You're an Anonymous Admin. Revert to your user account.", show_alert=True)
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(a, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
        chat_id = query.message.chat.id
        if chat_id in QUEUE:
            await leave_group_call_safe(chat_id)
            clear_queue(chat_id)
            await query.edit_message_text("✅ This streaming has ended", reply_markup=bcl)
        else:
            await query.answer("❌ Nothing is currently streaming", show_alert=True)
    except Exception as e:
        log.exception("cbstop error: %s", e)
        try:
            await query.edit_message_text(f"🚫 Error:\n`{e}`", reply_markup=bcl)
        except:
            await query.answer("An error occurred.", show_alert=True)


@bot.on_callback_query(filters.regex("cbmute"))
async def cbmute(_, query: CallbackQuery):
    try:
        if query.message.sender_chat:
            return await query.answer("You're an Anonymous Admin. Revert to your user account.", show_alert=True)
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(a, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
        chat_id = query.message.chat.id
        if chat_id in QUEUE:
            await mute_stream_safe(chat_id)
            await query.edit_message_text("🔇 Userbot successfully muted", reply_markup=bttn)
        else:
            await query.answer("❌ Nothing is currently streaming", show_alert=True)
    except Exception as e:
        log.exception("cbmute error: %s", e)
        try:
            await query.edit_message_text(f"🚫 Error:\n`{e}`", reply_markup=bcl)
        except:
            await query.answer("An error occurred.", show_alert=True)


@bot.on_callback_query(filters.regex("cbunmute"))
async def cbunmute(_, query: CallbackQuery):
    try:
        if query.message.sender_chat:
            return await query.answer("You're an Anonymous Admin. Revert to your user account.", show_alert=True)
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(a, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
        chat_id = query.message.chat.id
        if chat_id in QUEUE:
            await unmute_stream_safe(chat_id)
            await query.edit_message_text("🔊 Userbot successfully unmuted", reply_markup=bttn)
        else:
            await query.answer("❌ Nothing is currently streaming", show_alert=True)
    except Exception as e:
        log.exception("cbunmute error: %s", e)
        try:
            await query.edit_message_text(f"🚫 Error:\n`{e}`", reply_markup=bcl)
        except:
            await query.answer("An error occurred.", show_alert=True)


# ----------------------- volume command -----------------------
@bot.on_message(command(["volume", f"volume@{BOT_USERNAME}", "vol"]) & other_filters)
@authorized_users_only
async def change_volume(_, m: Message):
    try:
        # robust parsing
        if len(m.command) < 2:
            return await m.reply("Usage: /volume <0-200>")
        raw = m.command[1]
        try:
            vol = int(raw)
        except:
            return await m.reply("Volume must be an integer between 0 and 200.")
        if vol < 0 or vol > 200:
            return await m.reply("Volume must be between 0 and 200.")
        chat_id = m.chat.id
        if chat_id in QUEUE:
            await change_volume_safe(chat_id, vol)
            await m.reply(f"✅ Volume set to `{vol}%`")
        else:
            await m.reply("❌ Nothing is streaming.")
    except Exception as e:
        log.exception("change_volume error: %s", e)
        await m.reply(f"🚫 Error: `{e}`")


# ----------------------- skip callback (UI skip) -----------------------
@bot.on_callback_query(filters.regex("cbskip"))
async def cbskip(_, query: CallbackQuery):
    try:
        a = await _.get_chat_member(query.message.chat.id, query.from_user.id)
        if not getattr(a, "can_manage_voice_chats", False):
            return await query.answer("Only admins with manage voice chats permission can use this.", show_alert=True)
        chat_id = query.message.chat.id
        queue = await skip_current_song(chat_id)
        if queue == 0:
            return await query.answer("❌ Nothing is currently playing", show_alert=True)
        elif queue == 1:
            return await query.answer("» There's no more music in queue to skip, userbot leaving voice chat.", show_alert=True)
        elif queue == 2:
            return await query.answer("🗑️ Clearing the queue — userbot leaving voice chat.", show_alert=True)
        else:
            await query.answer("Skipping to next track...")
            # build UI and send thumbnail if possible
            try:
                user_id = query.from_user.id
                title = queue[0] if isinstance(queue, (list, tuple)) else str(queue)
                thumbnail = IMG_5
                gcname = query.message.chat.title
                ctitle = await CHAT_TITLE(gcname)
                image = await thumb(thumbnail, title, user_id, ctitle)
                buttons = []  # stream_markup may be repo-specific; try to import if exists
                try:
                    from RaiChu.inline import stream_markup

                    buttons = stream_markup(user_id)
                except Exception:
                    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="cbmenu")]]
                await _.send_photo(
                    chat_id,
                    photo=image,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    caption=f"⏭ Skipped to next track.\n\nName: [{title}]()\nChat: `{chat_id}`\nRequest by: [{query.from_user.first_name}](tg://user?id={user_id})",
                )
                # cleanup thumbnail if file created
                try:
                    remove_if_exists(image)
                except:
                    pass
            except Exception as e:
                log.exception("cbskip send photo error: %s", e)
                await query.message.reply_text("Skipped to next track.")
    except Exception as e:
        log.exception("cbskip error: %s", e)
        try:
            await query.answer("An error occurred.", show_alert=True)
        except:
            pass
