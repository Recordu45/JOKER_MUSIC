from typing import List, Union, Iterable
from pyrogram import filters
from RaiChu import config

# Ensure we have prefixes (fallback to common ones)
_COMMAND_PREFIXES = getattr(config, "COMMAND_PREFIXES", ["/", "!", "."])

# Filters used often in handlers: exclude edited, via_bot and forwarded messages
other_filters = filters.group & ~filters.edited & ~filters.via_bot & ~filters.forwarded
other_filters2 = filters.private & ~filters.edited & ~filters.via_bot & ~filters.forwarded

def command(commands: Union[str, List[str], Iterable[str]]):
    """
    Return a pyrogram command filter using configured COMMAND_PREFIXES.
    Accepts a single command string or an iterable of commands.

    Usage:
        @app.on_message(command("play"))
        async def handler(client, message): ...
    """
    if isinstance(commands, str):
        cmds = [commands]
    else:
        cmds = list(commands)

    # normalize to lower-case so handlers can be case-insensitive
    cmds = [c.lower() for c in cmds]

    return filters.command(cmds, prefixes=_COMMAND_PREFIXES)
