# Process/main.py — safe, Render-friendly version
import os
import asyncio
import logging
import traceback
from pyrogram import Client
from pyrogram import idle
from pytgcalls import PyTgCalls

# load config from env (or from RaiChu.config if you prefer)
# prefer environment for Render; keep backward compatibility with RaiChu.config
API_ID = int(os.environ.get("API_ID") or os.environ.get("RAICHU_API_ID") or 0)
API_HASH = os.environ.get("API_HASH") or os.environ.get("RAICHU_API_HASH") or ""
BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("RAICHU_BOT_TOKEN") or ""
SESSION_NAME = os.environ.get("SESSION_NAME") or "daaku"
SESSION_STRING = os.environ.get("SESSION_STRING")  # preferred: set this as Render secret

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Bot client (unchanged) ----------------
bot = Client(
    "RaiChu",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="RaiChu.Player"),
)

# ---------------- Assistant / user client ----------------
# Prefer session string (no file on disk). If not provided, fallback to file session.
if SESSION_STRING:
    logger.info("Using SESSION_STRING from environment for assistant (in-memory).")
    aman = Client(
        "assistant",            # name (won't create a persistent file when using session_string)
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
    )
else:
    logger.info("No SESSION_STRING found — falling back to file-based session (ensure .session is not corrupted).")
    aman = Client(
        SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
    )

# ---------------- PyTgCalls instance ----------------
call_py = PyTgCalls(aman, cache_duration=100, overload_quiet_mode=True)


# ---------------- Start / Stop helpers ----------------
async def start_clients():
    logger.info("Starting bot client...")
    await bot.start()
    logger.info("Bot started.")

    # start assistant and handle corrupted session gracefully
    logger.info("Starting assistant (user) client...")
    try:
        await aman.start()
    except Exception as e:
        # common symptom of corrupted session file: struct.error unpack requires a buffer...
        logger.exception("Assistant client failed to start. Possible corrupted session or invalid session string.")
        # give a clear actionable message in logs
        logger.error(
            "If you use a file-based session, delete the <SESSION_NAME>.session file on the server.\n"
            "If you use SESSION_STRING, ensure it is valid and belongs to a user account (not a bot token).\n"
            "Commands you can run in Render Shell:\n"
            "  find . -type f -name \"*.session\" -print\n"
            "  find . -type f -name \"*.session\" -delete\n"
            "Also check that SESSION_STRING env var is set in Render secrets."
        )
        # re-raise so process can exit or you can act on it (we keep it raised so deploy fails loudly)
        raise

    logger.info("Assistant client started.")

    logger.info("Starting PyTgCalls...")
    try:
        await call_py.start()
        logger.info("PyTgCalls started.")
    except Exception:
        logger.exception("Failed to start PyTgCalls. Ensure assistant account is a user (not a bot) and has access to voice chats.")
        raise

    # Log account info
    try:
        me_bot = await bot.get_me()
        me_aman = await aman.get_me()
        logger.info("Bot logged in as: %s (@%s) id=%s", getattr(me_bot, "first_name", ""), getattr(me_bot, "username", ""), getattr(me_bot, "id", ""))
        logger.info("Assistant logged in as: %s (@%s) id=%s is_bot=%s", getattr(me_aman, "first_name", ""), getattr(me_aman, "username", ""), getattr(me_aman, "id", ""), getattr(me_aman, "is_bot", None))
        if getattr(me_aman, "is_bot", False):
            logger.error("Assistant account is a bot. Voice chat joining requires a user account. Create a user session and set SESSION_STRING accordingly.")
    except Exception:
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


# ---------------- Convenience runner for local run ----------------
async def run_forever():
    await start_clients()
    try:
        logger.info("Entering idle state. Bot is running...")
        await idle()
    finally:
        logger.info("Shutting down...")
        await stop_clients()
        logger.info("Shutdown complete.")


# ---------------- Prevent accidental run on import ----------------
if __name__ == "__main__":
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — exiting.")
    except Exception:
        logger.exception("Unhandled exception in main.")
