# 🎨 Design Module

The **design** directory contains all visual styling elements used by the project.  
Anything related to thumbnails, banners, overlays, colors, typography, and layout logic is stored here.

## 📁 Purpose of This Folder
- Store reusable design components  
- Maintain consistent styles for thumbnails and UI elements  
- Provide color themes, spacing rules, and font settings  
- Keep image-related utilities separate from bot logic  

## 📦 Typical Files Inside
- `colors.py` — predefined color palettes  
- `shapes.py` — helper functions for rounded corners, shadows, masks  
- `layout.py` — thumbnail layout rules  
- `theme.py` — global theme configuration  
- `README.md` — this documentation  

## 🧩 Where It’s Used
This folder supports:
- Thumbnail generator  
- Song card renderer  
- Joker-style visual elements  
- Any image created under `Process/ImageFont/`  

## 📝 Notes
This folder does **not** store actual images.  
Image assets belong in `Process/ImageFont/` or external URLs.

---

Maintained for **JOKER_MUSIC** project.
