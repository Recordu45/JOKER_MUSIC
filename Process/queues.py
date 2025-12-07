from typing import Dict, List, Optional, Any

# Structure: { chat_id: [ {song info dict}, ... ] }
QUEUE: Dict[int, List[dict]] = {}


def add_to_queue(
    chat_id: int,
    songname: str,
    link: str,
    ref: Any,
    type: str,
    quality: str
) -> int:
    """
    Add a song item to queue.
    Returns index of newly added item.
    """

    item = {
        "title": songname,
        "link": link,
        "ref": ref,
        "type": type,
        "quality": quality
    }

    if chat_id not in QUEUE:
        QUEUE[chat_id] = []

    QUEUE[chat_id].append(item)
    return len(QUEUE[chat_id]) - 1


def get_queue(chat_id: int) -> List[dict]:
    """
    Return queue list for chat or an empty list.
    """
    return QUEUE.get(chat_id, [])


def get_next(chat_id: int) -> Optional[dict]:
    """
    Return the next song (first element) without removing it.
    """
    q = QUEUE.get(chat_id)
    if q and len(q) > 0:
        return q[0]
    return None


def pop_an_item(chat_id: int) -> Optional[dict]:
    """
    Pop the first item safely.
    Returns the popped item or None.
    """
    q = QUEUE.get(chat_id)
    if q and len(q) > 0:
        return q.pop(0)
    return None


def clear_queue(chat_id: int) -> bool:
    """
    Completely clear queue for chat.
    """
    if chat_id in QUEUE:
        del QUEUE[chat_id]
        return True
    return False


def queue_length(chat_id: int) -> int:
    """
    Return number of items in the queue.
    """
    return len(QUEUE.get(chat_id, []))


def remove_index(chat_id: int, index: int) -> Optional[dict]:
    """
    Remove a specific item by index.
    Returns removed item or None.
    """
    q = QUEUE.get(chat_id)
    if q and 0 <= index < len(q):
        return q.pop(index)
    return None
