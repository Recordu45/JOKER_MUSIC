from typing import List
from pyrogram.types import Chat
from Process.Cache.admins import get as cache_get, set as cache_set


async def get_administrators(chat: Chat) -> List[int]:
    """
    Return cached list of admin IDs who can manage voice chats.
    If not cached, fetch from Telegram, store, and return.
    """

    # try cached admins first
    cached = cache_get(chat.id)
    if cached:
        return cached

    try:
        # fetch admin members from Telegram
        admins = await chat.get_members(filter="administrators")
    except Exception:
        return []

    valid_admins = []

    for member in admins:
        user = member.user

        # ignore deleted accounts
        if not user or user.is_deleted:
            continue

        perms = member.privileges if hasattr(member, "privileges") else member
        if hasattr(perms, "can_manage_voice_chats") and perms.can_manage_voice_chats:
            valid_admins.append(user.id)

    # ensure list unique and sorted
    valid_admins = sorted(list(set(valid_admins)))

    # store in cache
    cache_set(chat.id, valid_admins)

    return valid_admins
