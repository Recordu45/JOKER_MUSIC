"""
Joker/config.py
Central configuration file for JOKER_MUSIC bot.
Loads environment variables and provides sane defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables
if os.path.exists("local.env"):
    load_dotenv("local.env")

load_dotenv()


# -------------------- REQUIRED VALUES --------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN is missing in environment variables!")

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

if not API_ID or not API_HASH:
    raise SystemExit("❌ API_ID and/or API_HASH are missing in environment variables!")


# -------------------- OPTIONAL / SAFE DEFAULTS --------------------

SESSION_NAME = os.getenv("SESSION_NAME", "JOKER_USER_SESSION")

BOT_NAME = os.getenv("BOT_NAME", "JOKER_MUSIC")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "JokerAssist")
ASSISTANT_USERNAME = os.getenv("ASSISTANT_USERNAME", "")
OWNER_NAME = os.getenv("OWNER_NAME", "Unknown")
ALIVE_NAME = os.getenv("ALIVE_NAME", "JOKER")

GROUP_SUPPORT = os.getenv("GROUP_SUPPORT", "")
UPDATES_CHANNEL = os.getenv("UPDATES_CHANNEL", "")

COMMAND_PREFIXES = os.getenv("COMMAND_PREFIXES", "/ ! .").split()


# -------------------- SUDO USERS --------------------

_raw_sudo = os.getenv("SUDO_USERS", "")

try:
    SUDO_USERS = list(map(int, _raw_sudo.split()))
except Exception:
    SUDO_USERS = []
    print("⚠ WARNING: SUDO_USERS malformed. Using empty list.")


# -------------------- DURATIONS --------------------

DURATION_LIMIT = int(os.getenv("DURATION_LIMIT", "60"))  # minutes


# -------------------- STATIC IMAGE URLS --------------------

ALIVE_IMG = os.getenv(
    "ALIVE_IMG",
    "https://telegra.ph/file/c83b000f004f01897fe18.png"
)

YOUTUBE_IMG_URL = os.getenv(
    "YOUTUBE_IMG_URL",
    "https://telegra.ph/file/58da23d726b601dc3b18e.jpg"
)

IMG_1 = os.getenv("IMG_1", "https://telegra.ph/file/d6f92c979ad96b2031cba.png")
IMG_2 = os.getenv("IMG_2", "https://telegra.ph/file/6213d2673486beca02967.png")
IMG_3 = os.getenv("IMG_3", "https://telegra.ph/file/f02efde766160d3ff52d6.png")
IMG_4 = os.getenv("IMG_4", "https://telegra.ph/file/be5f551acb116292d15ec.png")
IMG_5 = os.getenv("IMG_5", "https://telegra.ph/file/c3401a572375b569138c3.png")
IMG_6 = os.getenv("IMG_6", "https://telegra.ph/file/d8f8fc1de9110b93ca94c.jpg")


# -------------------- REPO LINK --------------------

UPSTREAM_REPO = os.getenv(
    "UPSTREAM_REPO",
    "https://github.com/Recordu45/JOKER_MUSIC"
)
