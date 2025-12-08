# RaiChu.Player

This folder contains the bot's player and group-related plugins (handlers) used by the RaiChu music bot.  
This README explains what each part does, how to set up locally and on Render, required environment variables, quick tests and common troubleshooting steps.

---

## Contents
- `Buger.py` — glitch/bug text generator command (`/bug`).
- `Broadcast.py` — safe broadcast command (`/gcast`).
- `Group.py` — group helpers: uptime, ping, start, help.
- `test_vc.py` *(optional)* — join/play test handlers (used for debugging VC & playback).
- Other plugin files (handlers) live here.

---

## Quick features & test commands
Use these commands in a private chat with the bot (or group where bot is active):
- `/start` — basic start info (group mode).
- `/ping` — latency check.
- `/uptime` — bot uptime (admins only if decorated).
- `/bug` (reply to a message) — turn text into glitchy/zalgo text.
- `/gcast` (reply to a message; SUDO only) — broadcast to dialogs (safe, rate-limited).
- `/join <chat_id>` and `/play <url_or_path>` — test VC join / play handlers (if `test_vc.py` installed).

---

## Required environment variables
Make sure the following env vars are set (Render secrets or `.env` locally):

- `API_ID` — Telegram API ID (from my.telegram.org)  
- `API_HASH` — Telegram API Hash  
- `BOT_TOKEN` — Bot token for bot-client (BotFather)  
- `SESSION_STRING` — **(preferred)** assistant user session string (phone login) — required for voice features  
- `SESSION_NAME` — (fallback) name for file-based session (not recommended on Render)  
- `SUDO_USERS` — comma separated list of admin ids (or configured in `RaiChu.config`)  
- `GROUP_SUPPORT`, `UPDATES_CHANNEL` etc. — used by group helpers

**Important:** For VC and PyTgCalls you must use a **USER** session (phone login). Bot tokens cannot join voice chats.

---

## Generate `SESSION_STRING` (recommended)
Generate locally on your laptop (free):

1. Save `gen_session.py`:
```py
import asyncio, os
from pyrogram import Client

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

async def main():
    async with Client(":memory:", api_id=API_ID, api_hash=API_HASH) as app:
        print(await app.export_session_string())

if __name__ == "__main__":
    asyncio.run(main())
