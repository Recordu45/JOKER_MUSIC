import asyncio
import sys
import traceback
from pyrogram import idle
from Process.main import call_py, bot

async def safe_start(obj, name="object"):
    """Start an object which may expose an async start() or sync start()."""
    if obj is None:
        return
    start_fn = getattr(obj, "start", None)
    if start_fn is None:
        return
    try:
        if asyncio.iscoroutinefunction(start_fn):
            await start_fn()
        else:
            # sync call
            start_fn()
    except Exception:
        print(f"[WARN]: Failed to start {name}:")
        traceback.print_exc()

async def safe_stop(obj, name="object"):
    """Stop an object which may expose an async stop() or sync stop()."""
    if obj is None:
        return
    stop_fn = getattr(obj, "stop", None)
    if stop_fn is None:
        return
    try:
        if asyncio.iscoroutinefunction(stop_fn):
            await stop_fn()
        else:
            # sync call
            stop_fn()
    except Exception:
        print(f"[WARN]: Failed to stop {name}:")
        traceback.print_exc()

async def main():
    print("[INFO]: STARTING BOT CLIENT")
    # start bot (this will perform time sync)
    await safe_start(bot, name="bot")

    print("[INFO]: STARTING PYTGCALLS CLIENT (if any)")
    await safe_start(call_py, name="pytgcalls/call_py")

    print("[INFO]: BOT IS RUNNING...")
    try:
        # pyrogram.idle will keep the program alive until SIGINT/SIGTERM
        await idle()
    except (KeyboardInterrupt, SystemExit):
        print("[INFO]: Received stop signal")
    finally:
        print("[INFO]: STOPPING PYTGCALLS (if running)")
        # stop voice client first to prevent cleanup from running after loop is closed
        await safe_stop(call_py, name="pytgcalls/call_py")

        print("[INFO]: STOPPING BOT")
        await safe_stop(bot, name="bot")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[INFO]: BOT STOPPED (keyboard interrupt)")
    except Exception:
        print("[ERROR]: Fatal exception in main()")
        traceback.print_exc()
        # exit non-zero so Render shows failure
        sys.exit(1)
