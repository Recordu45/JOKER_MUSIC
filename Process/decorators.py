from typing import Callable, List, Any
from pyrogram import Client
from pyrogram.types import Message
from RaiChu.config import SUDO_USERS
from Process.admins import get_administrators
import traceback


# --------------- SAFE ERROR DECORATOR ---------------- #

def errors(func: Callable) -> Callable:
    async def wrapper(client: Client, message: Message):
        try:
            return await func(client, message)
        except Exception as e:
            err_text = f"**Error:** `{type(e).__name__}`\n`{str(e)}`"
            try:
                await message.reply(err_text)
            except Exception:
                pass  # ignore if cannot send message
            print("ERROR in handler:", func.__name__)
            traceback.print_exc()

    return wrapper


# --------------- CHECK IF USER IS AUTHORIZED (SUDO + ADMINS) ---------------- #

def authorized_users_only(func: Callable) -> Callable:
    async def wrapper(client: Client, message: Message):

        user = message.from_user
        if user is None:
            return  # skip anonymous admins or service messages

        uid = user.id

        # SUDO override
        if uid in SUDO_USERS:
            return await func(client, message)

        # Cache-based admin list
        admin_ids = await get_administrators(message.chat)
        if uid in admin_ids:
            return await func(client, message)

        # unauthorized → silently ignore
        return

    return wrapper


# --------------- SUDO ONLY ---------------- #

def sudo_users_only(func: Callable) -> Callable:
    async def wrapper(client: Client, message: Message):

        user = message.from_user
        if user is None:
            return

        if user.id in SUDO_USERS:
            return await func(client, message)

        # User should know command is sudo locked
        try:
            await message.reply("⚠️ This command is only for SUDO users.")
        except Exception:
            pass

    return wrapper


# --------------- BYTES → HUMAN READABLE ---------------- #

def humanbytes(size: int) -> str:
    """Convert size in bytes to human readable string."""
    if size is None:
        return "0 B"

    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PiB"
