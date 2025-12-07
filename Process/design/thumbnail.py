import os
import re
import textwrap
import io
import traceback
from typing import Optional

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch

from RaiChu.config import BOT_NAME, YOUTUBE_IMG_URL

# Constants
CANVAS_W = 1280
CANVAS_H = 720
ALBUM_SIZE = 520
FONT_PATH_PRIMARY = os.path.join("Process", "ImageFont", "font.ttf")
FONT_PATH_SECOND = os.path.join("Process", "ImageFont", "font2.ttf")


def _change_image_size(max_width: int, max_height: int, image: Image.Image) -> Image.Image:
    """Resize image preserving aspect ratio to fit within max_width x max_height."""
    w, h = image.size
    ratio = min(max_width / w, max_height / h)
    new_size = (int(w * ratio), int(h * ratio))
    return image.resize(new_size, Image.LANCZOS)


async def _download_image_bytes(url: str, session: aiohttp.ClientSession, timeout: int = 15) -> bytes:
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.read()


def _load_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype(FONT_PATH_PRIMARY, size)
        except Exception:
            return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int):
    lines = []
    for paragraph in textwrap.wrap(text, width=40):
        # further ensure lines fit
        current = ""
        for word in paragraph.split():
            test = (current + " " + word).strip()
            w, _ = ImageDraw.Draw(Image.new("RGB", (1, 1))).textsize(test, font=font)
            if w <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


async def _fetch_youtube_info(videoid: str) -> Optional[dict]:
    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        res = await results.next()
        if not res or "result" not in res or not res["result"]:
            return None
        info = res["result"][0]
        title = info.get("title", "Unsupported Title")
        title = re.sub(r"\s+", " ", re.sub(r"\W+", " ", title)).strip().title()
        duration = info.get("duration", "Unknown Mins")
        thumbnails = info.get("thumbnails", [])
        thumb_url = thumbnails[0]["url"].split("?")[0] if thumbnails else None
        views = info.get("viewCount", {}).get("short", "Unknown Views")
        channel = info.get("channel", {}).get("name", "Unknown Channel")
        return {
            "title": title,
            "duration": duration,
            "thumbnail": thumb_url,
            "views": views,
            "channel": channel,
        }
    except Exception:
        return None


async def _create_base(canvas_w: int = CANVAS_W, canvas_h: int = CANVAS_H, thumb_img: Optional[Image.Image] = None):
    # Create gradient-like background from the thumbnail (blur + darken)
    if thumb_img:
        bg = thumb_img.copy().convert("RGBA")
        bg = _change_image_size(canvas_w, canvas_h, bg)
        bg = bg.filter(ImageFilter.BoxBlur(30))
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.55)
        base = Image.new("RGBA", (canvas_w, canvas_h))
        base.paste(bg, ((canvas_w - bg.width) // 2, (canvas_h - bg.height) // 2))
    else:
        base = Image.new("RGBA", (canvas_w, canvas_h), (18, 18, 18, 255))
    return base


def _paste_album(canvas: Image.Image, album: Image.Image, x: int = 50, y: int = 100):
    # Crop centered square from album, make rounded, add border and soft shadow
    w = album.width
    h = album.height
    side = min(w, h)
    cx = w // 2
    cy = h // 2
    left = cx - side // 2
    top = cy - side // 2
    album_crop = album.crop((left, top, left + side, top + side)).convert("RGBA")
    album_crop.thumbnail((ALBUM_SIZE, ALBUM_SIZE), Image.LANCZOS)

    # shadow
    shadow = Image.new("RGBA", (ALBUM_SIZE + 40, ALBUM_SIZE + 40), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(shadow)
    sh_draw.ellipse((0, 0, ALBUM_SIZE + 40, ALBUM_SIZE + 40), fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(shadow, (x - 20, y - 20), shadow)

    # rounded mask
    mask = Image.new("L", (ALBUM_SIZE, ALBUM_SIZE), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (ALBUM_SIZE, ALBUM_SIZE)], radius=30, fill=255)
    # border
    bordered = ImageOps.expand(album_crop, border=12, fill="white")
    # paste centered on mask area
    canvas.paste(bordered, (x, y), mask)


async def _make_thumbnail_from_info(info: dict, prefix: str, videoid: str) -> Optional[str]:
    title = info.get("title", "Unsupported Title")
    duration = info.get("duration", "Unknown Mins")
    thumb_url = info.get("thumbnail")
    views = info.get("views", "Unknown Views")
    channel = info.get("channel", "Unknown Channel")

    out_name = f"{prefix}{videoid}.png"

    try:
        # download thumbnail bytes (if available)
        thumb_img = None
        if thumb_url:
            async with aiohttp.ClientSession() as session:
                try:
                    img_bytes = await _download_image_bytes(thumb_url, session)
                    thumb_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                except Exception:
                    thumb_img = None

        canvas = await _create_base(thumb_img=thumb_img)

        # album area
        album_x = 50
        album_y = (CANVAS_H - ALBUM_SIZE) // 2
        if thumb_img:
            _paste_album(canvas, thumb_img, x=album_x, y=album_y)
        else:
            # placeholder square
            placeholder = Image.new("RGBA", (ALBUM_SIZE, ALBUM_SIZE), (30, 30, 30))
            _paste_album(canvas, placeholder, x=album_x, y=album_y)

        draw = ImageDraw.Draw(canvas)
        # fonts with fallback
        title_font = _load_font(FONT_PATH_SECOND if os.path.exists(FONT_PATH_SECOND) else FONT_PATH_PRIMARY, 72)
        main_font = _load_font(FONT_PATH_SECOND if os.path.exists(FONT_PATH_SECOND) else FONT_PATH_PRIMARY, 40)
        small_font = _load_font(FONT_PATH_PRIMARY, 30)
        footer_font = _load_font(FONT_PATH_PRIMARY, 22)

        right_x = album_x + ALBUM_SIZE + 60
        max_w = CANVAS_W - right_x - 80

        # BOT name (top-left)
        try:
            bot_font = _load_font(FONT_PATH_PRIMARY, 28)
            draw.text((5, 5), f"{BOT_NAME}", fill="white", font=bot_font)
        except Exception:
            pass

        # Title block
        title_lines = _wrap_text(title, title_font, max_w)
        y_text = (CANVAS_H // 2) - (len(title_lines) * 42)
        for line in title_lines[:3]:  # limit lines to 3
            # shadow
            draw.text((right_x + 3, y_text + 3), line, font=title_font, fill=(0, 0, 0, 200))
            # main text with stroke
            draw.text((right_x, y_text), line, font=title_font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
            y_text += 78

        # small meta lines
        y_meta = y_text + 6
        if channel:
            draw.text((right_x, y_meta), f"Channel: {channel}", font=main_font, fill=(220, 220, 220))
            y_meta += 44
        if views:
            draw.text((right_x, y_meta), f"Views: {views}", font=main_font, fill=(220, 220, 220))
            y_meta += 36
        if duration:
            draw.text((right_x, y_meta), f"Duration: {duration}", font=main_font, fill=(220, 220, 220))
            y_meta += 36

        # footer
        footer_text = f"Powered by {os.getenv('BOT_NAME', BOT_NAME)}"
        draw.text((right_x, CANVAS_H - 60), footer_text, font=footer_font, fill=(180, 180, 180))

        # finalize: rounded corners mask
        final = Image.new("RGBA", canvas.size)
        final.paste(canvas, (0, 0))
        mask = Image.new("L", final.size, 255)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([(0, 0), final.size], radius=28, fill=255)
        final.putalpha(mask)

        out_rgb = final.convert("RGB")
        out_rgb.save(out_name, quality=88, optimize=True)
        return out_name
    except Exception:
        # debug print
        traceback.print_exc()
        return None


async def play_thumb(videoid: str) -> str:
    """
    Generate a 'NOW PLAYING' thumbnail for a YouTube video id.
    Returns path of generated file or fallback YOUTUBE_IMG_URL.
    """
    try:
        info = await _fetch_youtube_info(videoid)
        if not info:
            return YOUTUBE_IMG_URL

        out = await _make_thumbnail_from_info(info, prefix="pfinal_", videoid=videoid)
        return out or YOUTUBE_IMG_URL
    except Exception:
        traceback.print_exc()
        return YOUTUBE_IMG_URL


async def queue_thumb(videoid: str) -> str:
    """
    Generate an 'IN QUEUE' thumbnail for a YouTube video id.
    Returns path of generated file or fallback YOUTUBE_IMG_URL.
    """
    try:
        info = await _fetch_youtube_info(videoid)
        if not info:
            return YOUTUBE_IMG_URL

        # change title of block to 'IN QUEUE' by temporarily adding it to title
        info_copy = dict(info)
        info_copy["title"] = info_copy.get("title", "")
        out = await _make_thumbnail_from_info(info_copy, prefix="qfinal_", videoid=videoid)
        return out or YOUTUBE_IMG_URL
    except Exception:
        traceback.print_exc()
        return YOUTUBE_IMG_URL
