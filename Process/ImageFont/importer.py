import os
import requests
from PIL import Image
from io import BytesIO

ROOT = os.path.dirname(os.path.dirname(__file__))
FONT_PATH = os.path.join(ROOT, "ImageFont", "font.ttf")

def load_image(path_or_url: str, size=(512, 512)) -> Image.Image:
    """
    Load image from local path or URL and return a PIL Image resized to `size`.
    """
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        resp = requests.get(path_or_url, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
    else:
        img = Image.open(path_or_url).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)
    return img
