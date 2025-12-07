import os
import uuid
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps

from Process.design.thumbnail import changeImageSize   # safe reuse
from Process.design.chatname import CHAT_TITLE

# fallback font paths
FONT_MAIN = "Process/ImageFont/finalfont.ttf"
FONT_SECOND = "Process/ImageFont/finalfont.ttf"  # same font, can change later
OVERLAY_IMAGE = "Process/ImageFont/Red.png"


def safe_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


async def thumb(title: str, thumbnail: str, userid: int, ctitle: str):
    """
    Create a modern, safe thumbnail for 'Playing On: Chat Name' + title.
    Returns path of final saved PNG image.
    """

    # sanitize ctitle
    clean_ctitle = await CHAT_TITLE(ctitle)
    short_title = (title[:27] + "...") if len(title) > 27 else title
    short_chat = (clean_ctitle[:14] + "...") if len(clean_ctitle) > 14 else clean_ctitle

    # unique temp name to avoid conflicts
    uid = uuid.uuid4().hex
    bg_temp = f"bg_{uid}.png"
    final_out = f"final_{uid}.png"

    # download thumbnail
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(bg_temp, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return None
    except Exception:
        return None

    try:
        # load and resize background image
        bg_img = Image.open(bg_temp).convert("RGBA")
        bg_img = changeImageSize(1280, 720, bg_img)

        # overlay image (PNG with transparent design)
        overlay = Image.open(OVERLAY_IMAGE).convert("RGBA")
        overlay = changeImageSize(1280, 720, overlay)

        # composite both layers
        composed = Image.alpha_composite(bg_img, overlay)

        # draw text
        draw = ImageDraw.Draw(composed)
        font_title = safe_font(FONT_MAIN, 85)
        font_chat = safe_font(FONT_SECOND, 60)

        # text placement
        draw.text(
            (20, 45),
            f"Playing on: {short_chat}",
            fill="white",
            stroke_width=2,
            stroke_fill="black",
            font=font_chat,
        )

        draw.text(
            (25, 595),
            f"{short_title}",
            fill="white",
            stroke_width=2,
            stroke_fill="black",
            font=font_title,
        )

        composed.save(final_out)

    except Exception:
        return None

    finally:
        # cleanup temp file
        if os.path.exists(bg_temp):
            os.remove(bg_temp)

    return final_out
