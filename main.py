import asyncio
import sys
import traceback
import os
from aiohttp import web
from pyrogram import idle
from Process.main import call_py, bot


async def safe_start(obj, name="object"):
    if obj is None:
        return
    start_fn = getattr(obj, "start", None)
    if start_fn is None:
        return
    try:
        if asyncio.iscoroutinefunction(start_fn):
            await start_fn()
        else:
            start_fn()
    except Exception:
        print(f"[WARN]: Failed to start {name}:")
        traceback.print_exc()


async def safe_stop(obj, name="object"):
    if obj is None:
        return
    stop_fn = getattr(obj, "stop", None)
    if stop_fn is None:
        return
    try:
        if asyncio.iscoroutinefunction(stop_fn):
            await stop_fn()
        else:
            stop_fn()
    except Exception:
        print(f"[WARN]: Failed to stop {name}:")
        traceback.print_exc()


# ============================ HEALTH SERVER ============================

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


# ============================= MAIN BOT ================================

async def main():
    print("[INFO]: STARTING BOT CLIENT")
    await safe_start(bot, name="bot")

    print("[INFO]: STARTING PYTGCALLS CLIENT")
    await safe_start(call_py, name="pytgcalls/call_py")

    # Start HTTP server for Render
    health_runner = await start_health_server()

    print("[INFO]: BOT IS RUNNING...")
    try:
        await idle()
    except (KeyboardInterrupt, SystemExit):
        print("[INFO]: Received stop signal")
    finally:
        print("[INFO]: STOPPING PYTGCALLS")
        await safe_stop(call_py, name="pytgcalls/call_py")

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
