import os
import asyncio
import logging
import traceback
from pyrogram import Client, idle
from pytgcalls import PyTgCalls

API_ID = int(os.environ.get("API_ID") or 0)
API_HASH = os.environ.get("API_HASH") or ""
BOT_TOKEN = os.environ.get("BOT_TOKEN") or ""
SESSION_NAME = os.environ.get("SESSION_NAME") or "assistant"
SESSION_STRING = os.environ.get("SESSION_STRING")  # preferred

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- BOT CLIENT ----------------
bot = Client(
    "RaiChu",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="RaiChu.Player"),
)

# ---------------- ASSISTANT CLIENT ----------------
if SESSION_STRING:
    logger.info("Using SESSION_STRING for assistant (in-memory session).")
    aman = Client(
        "assistant_mem",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
    )
else:
    logger.info("Using file-based session (fallback).")
    aman = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    )

# ---------------- PYTGCALLS ----------------
call_py = PyTgCalls(aman)


# -------------- STARTUP LOGIC --------------
async def start_clients():
    logger.info("Starting bot...")
    await bot.start()
    logger.info("Bot started.")

    logger.info("Testing assistant session...")
    try:
        await aman.start()
        me = await aman.get_me()
        logger.info(f"Assistant logged in as: {me.first_name} (@{me.username}) is_bot={me.is_bot}")

        if me.is_bot:
            logger.error("❌ ERROR: Assistant account is a BOT. VC join NEVER works with bot accounts.")
            logger.error("👉 Fix: Create SESSION_STRING using USER (phone login), not bot token.")
            raise SystemExit

    except Exception:
        logger.error("❌ Assistant failed to start. SESSION_STRING may be invalid or corrupted.")
        logger.error("👉 Fix: Generate new SESSION_STRING on your phone/laptop.")
        traceback.print_exc()
        raise SystemExit

    logger.info("Starting PyTgCalls...")
    try:
        await call_py.start()
        logger.info("PyTgCalls started successfully.")
    except Exception:
        logger.error("❌ PyTgCalls failed to start. Assistant must be USER and must start correctly.")
        traceback.print_exc()
        raise SystemExit


# -------------- CLEAN SHUTDOWN --------------
async def stop_clients():
    try:
        await call_py.stop()
    except:
        pass
    try:
        await aman.stop()
    except:
        pass
    try:
        await bot.stop()
    except:
        pass


# -------------- MAIN LOOP --------------
async def run_forever():
    await start_clients()
    await idle()
    await stop_clients()


if __name__ == "__main__":
    try:
        asyncio.run(run_forever())
    except:
        traceback.print_exc()
