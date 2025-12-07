import os
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(__file__))
FONT_PATH = os.path.join(ROOT, "ImageFont", "font.ttf")

CANVAS_W = 1280
CANVAS_H = 720
ALBUM_SIZE = 480  # square album art

def _load_font(size: int):
    return ImageFont.truetype(FONT_PATH, size)

def _rounded_rectangle(im, radius):
    """Return mask for rounded corners."""
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    w, h = im.size
    draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    return mask

def _make_gradient(w, h, top_color, bottom_color):
    base = Image.new("RGB", (w, h), top_color)
    top = Image.new("RGB", (w, h), bottom_color)
    mask = Image.new("L", (w, h))
    for y in range(h):
        mask.putpixel((0, y), int(255 * (y / h)))
    mask = mask.resize((w, h))
    grad = Image.composite(base, top, mask)
    return grad

def _draw_text_with_stroke(draw, xy, text, font, fill, stroke_fill, stroke_width):
    # Pillow supports stroke_width and stroke_fill in text() (Pillow >= 8.0)
    draw.text(xy, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)

def generate_song_card(
    title: str,
    artist: str = "",
    duration: str = "",
    album_art: Optional[str] = None,
    output_path: str = "thumbnail.jpg"
) -> str:
    """
    Generate a 1280x720 song thumbnail.
    - title: song title (big)
    - artist: artist / album (small)
    - duration: e.g. 03:45 (small)
    - album_art: optional local path or URL for album image
    - output_path: where to save final jpg
    Returns output_path.
    """
    # canvas + gradient background
    bg = _make_gradient(CANVAS_W, CANVAS_H, (18, 18, 18), (44, 12, 60))
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
    canvas.paste(bg, (0, 0))

    draw = ImageDraw.Draw(canvas)

    # album area (left)
    album_x = 80
    album_y = (CANVAS_H - ALBUM_SIZE) // 2

    if album_art:
        try:
            from .importer import load_image
            album = load_image(album_art, size=(ALBUM_SIZE, ALBUM_SIZE)).convert("RGBA")
        except Exception:
            album = Image.new("RGBA", (ALBUM_SIZE, ALBUM_SIZE), (30, 30, 30))
    else:
        # placeholder
        album = Image.new("RGBA", (ALBUM_SIZE, ALBUM_SIZE), (30, 30, 30))

    # add subtle border and shadow for album
    shadow = Image.new("RGBA", (ALBUM_SIZE + 40, ALBUM_SIZE + 40), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(shadow)
    sh_draw.ellipse((0, 0, ALBUM_SIZE + 40, ALBUM_SIZE + 40), fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(shadow, (album_x - 20, album_y - 20), shadow)

    # rounded album
    mask = Image.new("L", (ALBUM_SIZE, ALBUM_SIZE), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([(0, 0), (ALBUM_SIZE, ALBUM_SIZE)], radius=30, fill=255)
    canvas.paste(album, (album_x, album_y), mask)

    # right side texts
    right_x = album_x + ALBUM_SIZE + 60
    max_w = CANVAS_W - right_x - 80

    # Title
    title_font = _load_font(72)
    # measure and wrap if needed
    def _wrapped_text(text, font, max_width):
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            test = f"{cur} {w}".strip()
            if ImageDraw.Draw(Image.new("RGB", (1,1))).textsize(test, font=font)[0] <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    title_lines = _wrapped_text(title, title_font, max_w)
    # draw shadow first (slightly offset)
    y_text = (CANVAS_H // 2) - 40 - (len(title_lines)-1)*40
    for line in title_lines:
        # shadow
        draw.text((right_x+3, y_text+3), line, font=title_font, fill=(0,0,0,180))
        # stroke + fill
        draw.text((right_x, y_text), line, font=title_font, fill=(255,255,255), stroke_width=2, stroke_fill=(0,0,0))
        y_text += 78

    # artist
    if artist:
        artist_font = _load_font(36)
        y_text += 10
        draw.text((right_x, y_text), artist, font=artist_font, fill=(200,200,200))

    # duration bottom-right
    if duration:
        dur_font = _load_font(28)
        w_dur, h_dur = draw.textsize(duration, font=dur_font)
        draw.rectangle([(CANVAS_W - 80 - w_dur - 20, CANVAS_H - 80 - h_dur - 10),
                        (CANVAS_W - 80, CANVAS_H - 80 + 10)], fill=(0,0,0,120))
        draw.text((CANVAS_W - 80 - w_dur - 10, CANVAS_H - 80 - h_dur), duration, font=dur_font, fill=(255,255,255))

    # footer small: bot name
    footer_font = _load_font(22)
    footer_text = f"Powered by {os.getenv('BOT_NAME', 'JOKER_MUSIC')}"
    draw.text((right_x, CANVAS_H - 60), footer_text, font=footer_font, fill=(180,180,180))

    # finalize: rounded corners for whole image
    final = Image.new("RGBA", canvas.size)
    final.paste(canvas, (0, 0))
    mask = _rounded_rectangle(final, radius=28)
    final.putalpha(mask)

    # convert to RGB and save as JPEG
    out = final.convert("RGB")
    out.save(output_path, quality=88, optimize=True)
    return output_path
