"""Render the app icon to assets/ViberPrivacyBlur.ico (multi-size)."""
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])

from viberblur.brand import make_pixmap  # noqa: E402

assets = os.path.join(PROJ, "assets")
os.makedirs(assets, exist_ok=True)
png = os.path.join(assets, "icon256.png")
make_pixmap(256).save(png)

from PIL import Image  # noqa: E402

img = Image.open(png).convert("RGBA")
ico = os.path.join(assets, "ViberPrivacyBlur.ico")
img.save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("ICO written:", ico)
