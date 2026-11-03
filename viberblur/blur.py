"""Turn a captured PIL image into a frosted QPixmap.

Downscale -> Gaussian blur -> upscale. Doing the blur on a shrunken image is
both much cheaper and frostier than blurring at full resolution, so even the
one-time cost on activation is tiny. intensity (0..100) drives how far it
shrinks and how wide the blur is.
"""

from PIL import Image, ImageFilter
from PySide6.QtGui import QImage, QPixmap


def blur_to_pixmap(img: Image.Image, intensity: int) -> QPixmap:
    width, height = img.size
    intensity = max(0, min(100, int(intensity)))
    frac = intensity / 100.0
    factor = 3.0 + frac * 27.0   # shrink 3x .. 30x
    radius = 2.0 + frac * 10.0   # gaussian 2 .. 12
    sw = max(1, int(width / factor))
    sh = max(1, int(height / factor))
    small = img.resize((sw, sh), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(radius=radius))
    frosted = small.resize((width, height), Image.BILINEAR)
    return _pil_to_pixmap(frosted)


def _pil_to_pixmap(img: Image.Image) -> QPixmap:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
    # .copy() detaches the QImage from the Python bytes buffer before it is GC'd.
    return QPixmap.fromImage(qimg.copy())
