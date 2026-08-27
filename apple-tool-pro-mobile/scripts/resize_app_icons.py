from pathlib import Path

from PIL import Image

asset_dir = Path(__file__).resolve().parents[1] / "assets" / "images"
source = asset_dir / "icon.png"

with Image.open(source) as image:
    icon = image.convert("RGBA")
    icon.thumbnail((512, 512), Image.Resampling.LANCZOS)
    for name in ("icon.png", "splash-icon.png", "favicon.png", "android-icon-foreground.png"):
        icon.save(asset_dir / name, format="PNG", optimize=True, compress_level=9)
