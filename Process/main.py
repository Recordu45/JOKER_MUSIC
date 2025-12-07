import asyncio
import logging
from pyrogram import Client      # correct
from pyrogram import idle        # correct idle
from pytgcalls import PyTgCalls

from RaiChu.config import API_ID, API_HASH, BOT_TOKEN, SESSION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot client
bot = Client(
    "RaiChu",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="RaiChu.Player"),
)

# User client (assistant)
# FIX: remove session_name=
aman = Client(
    SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
)

# PyTgCalls instance
call_py = PyTgCalls(aman, cache_duration=100, overload_quiet_mode=True)


async def start_clients():
    logger.info("Starting bot client...")
    await bot.start()
    logger.info("Bot started.")

    logger.info("Starting assistant client...")
    await aman.start()
    logger.info("Assistant client started.")

    logger.info("Starting PyTgCalls...")
    await call_py.start()
    logger.info("PyTgCalls started.")

    # Log info
    try:
        me_bot = await bot.get_me()
        me_aman = await aman.get_me()
        logger.info(f"Bot logged in as: {me_bot.first_name} (@{me_bot.username})")
        logger.info(f"User logged in as: {me_aman.first_name} (@{me_aman.username})")
    except:
        logger.exception("Failed to fetch account info.")


async def stop_clients():
    logger.info("Stopping PyTgCalls...")
    try:
        await call_py.stop()
    except Exception:
        logger.exception("Error stopping PyTgCalls")

    logger.info("Stopping assistant client...")
    try:
        await aman.stop()
    except Exception:
        logger.exception("Error stopping assistant client.")

    logger.info("Stopping bot client...")
    try:
        await bot.stop()
    except Exception:
        logger.exception("Error stopping bot client.")


async def run_forever():
    await start_clients()
    try:
        logger.info("Entering idle state. Bot is running...")
        await idle()  # CORRECT idle
    finally:
        logger.info("Shutting down...")
        await stop_clients()
        logger.info("Shutdown complete.")


# prevent double execution when imported
if __name__ == "__main__":
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — exiting.")
    except Exception:
        logger.exception("Unhandled exception in main.")
