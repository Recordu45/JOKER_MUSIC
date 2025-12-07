import asyncio
import logging
from pyrogram import Client
from pytgcalls import PyTgCalls, idle

from RaiChu.config import API_ID, API_HASH, BOT_TOKEN, SESSION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Public clients (importable)
bot = Client(
    "RaiChu",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="RaiChu.Player"),
)

# User/client session (assistant user) - used by PyTgCalls
aman = Client(
    session_name=SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
)

# PyTgCalls instance bound to the user client (aman)
call_py = PyTgCalls(aman, cache_duration=100, overload_quiet_mode=True)


async def start_clients():
    """
    Start bot (bot client), aman (user client) and PyTgCalls.
    Call this once when launching the app.
    """
    logger.info("Starting bot client...")
    await bot.start()
    logger.info("Bot started.")

    logger.info("Starting user client (assistant)...")
    await aman.start()
    logger.info("Assistant client started.")

    logger.info("Starting PyTgCalls...")
    await call_py.start()
    logger.info("PyTgCalls started.")

    # optional: fetch and log identification info
    try:
        me_bot = await bot.get_me()
        me_aman = await aman.get_me()
        logger.info("Logged in as bot: %s (@%s)", getattr(me_bot, "first_name", ""), getattr(me_bot, "username", ""))
        logger.info("Logged in as user: %s (@%s)", getattr(me_aman, "first_name", ""), getattr(me_aman, "username", ""))
    except Exception:
        logger.exception("Failed to fetch account info.")


async def stop_clients():
    """
    Stop call_py, aman and bot clients in the correct order.
    """
    logger.info("Stopping PyTgCalls...")
    try:
        await call_py.stop()
    except Exception:
        logger.exception("Error stopping PyTgCalls.")

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
    """
    Start everything and keep process alive until interrupted.
    Suitable entrypoint for Docker/Heroku/Render workers.
    """
    await start_clients()
    try:
        logger.info("Entering idle state. Bot is now running.")
        await idle()  # wait until Ctrl+C / SIGTERM
    finally:
        logger.info("Shutting down clients...")
        await stop_clients()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    # If run directly, start the clients and block until stopped.
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — exiting.")
    except Exception:
        logger.exception("Unhandled exception in main.")
