from typing import Dict, List, Optional

# Cache of admin IDs by chat_id
admins: Dict[int, List[int]] = {}


def set_admins(chat_id: int, admin_list: List[int]) -> None:
    """Store admin IDs for a chat."""
    admins[chat_id] = admin_list


def get_admins(chat_id: int) -> List[int]:
    """Return admin IDs for a chat; empty list if not found."""
    return admins.get(chat_id, [])


def clear_admins(chat_id: int) -> None:
    """Clear admin list for a specific chat."""
    if chat_id in admins:
        del admins[chat_id]


def reset_all() -> None:
    """Completely clear all admin cache."""
    admins.clear()
