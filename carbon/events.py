import inspect
import logging
import sys
import re

from pathlib import Path
from telethon import events

def register(**args):
    """
    Registers a new message event for Telethon.

    Usage:
        @bot.on(register(pattern="^/start"))
        async def handler(event):
            ...

    This function:
    - ensures the pattern is case-insensitive by prepending (?i) when needed
    - replaces a leading '^/' with a pattern that matches common command prefixes
    - returns a telethon.events.NewMessage instance configured with the final args
    """
    pattern = args.get("pattern", None)
    r_pattern = r"^[/!.]"

    if pattern:
        # make pattern case-insensitive if not already
        if not pattern.startswith("(?i)"):
            pattern = "(?i)" + pattern

        # replace leading "^/" with r_pattern only once
        pattern = pattern.replace("^/", r_pattern, 1)

        # put the final pattern back into args
        args["pattern"] = pattern

    return events.NewMessage(**args)
