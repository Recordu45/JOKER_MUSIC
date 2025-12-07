import asyncio
import sys
import traceback
import os
import inspect
from aiohttp import web
from pyrogram import idle
from Process.main import call_py, bot


# ===================== SAFE START / STOP =====================

async def safe_start(obj, name="object"):
    """Start object; await if coroutine is returned."""
    if obj is None:
        print(f"[DEBUG] No {name} to start.")
        return

    start_fn = getattr(obj, "start", None)
    if start_fn is None:
        print(f"[DEBUG] {name} has no start()")
        return

    try:
        result = start_fn()
        if inspect.isawaitable(result):
            await result
        print(f"[INFO]: {name} started successfully.")
    except Exception:
        print(f"[WARN]: Failed to start {name}:")
        traceback.print_exc()


async def safe_stop(obj, name="object"):
    """Stop object; await if coroutine is returned."""
    if obj is None:
        print(f"[DEBUG] No {name} to stop.")
        return

    stop_fn = getattr(obj, "stop", None)
    if stop_fn is None:
        print(f"[DEBUG] {name} has no stop()")
        return

    try:
        result = stop_fn()
        if inspect.isawaitable(result):
            await result
        print(f"[INFO]: {name} stopped successfully.")
    except Exception:
        print(f"[WARN]: Failed to stop {name}:")
        traceback.print_exc()


# ====================== HEALTH SERVER ========================

async def start_health_server():
    port = int(os.environ.get("PORT", 8080))

    async def handle(request):
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"[INFO]: Health server running on port {port}")
    return runner


async def stop_health_server(runner):
    try:
        await runner.cleanup()
    except:
        pass


# ========================== MAIN BOT ==========================

async def main():
    print("[INFO]: STARTING BOT CLIENT")
    await safe_start(bot, name="bot")

    print("[INFO]: STARTING PYTGCALLS CLIENT")
    await safe_start(call_py, name="pytgcalls")

    # Start HTTP server for Render
    health_runner = await start_health_server()

    print("[INFO]: BOT IS RUNNING...")
    try:
        await idle()
    except (KeyboardInterrupt, SystemExit):
        print("[INFO]: Received stop signal")
    finally:
        print("[INFO]: STOPPING PYTGCALLS")
        await safe_stop(call_py, name="pytgcalls")

        print("[INFO]: STOPPING BOT")
        await safe_stop(bot, name="bot")

        print("[INFO]: STOPPING HEALTH SERVER")
        await stop_health_server(health_runner)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[INFO]: BOT STOPPED")
    except Exception:
        print("[ERROR]: Fatal exception in main()")
        traceback.print_exc()
        sys.exit(1)
