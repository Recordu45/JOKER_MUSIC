import asyncio
from pytgcalls import idle
from Process.main import call_py, bot

async def start_bot():
    print("[INFO]: STARTING BOT CLIENT")
    await bot.start()

    print("[INFO]: STARTING PYTGCALLS CLIENT")
    await call_py.start()

    print("[INFO]: BOT IS RUNNING...")
    await idle()

    print("[INFO]: STOPPING BOT & USERBOT")
    await bot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("[INFO]: BOT STOPPED")
