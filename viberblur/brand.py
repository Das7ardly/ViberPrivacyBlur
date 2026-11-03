"""App icon / logo drawn in code so there are no image assets to ship and it
recolours from one place."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

ACCENT = "#7360F2"  # Viber-ish violet


def make_pixmap(size: int = 64) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = size * 0.22
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(ACCENT))
    p.drawRoundedRect(QRectF(size * 0.06, size * 0.06, size * 0.88, size * 0.88), r, r)

    # An eye (privacy) with a diagonal slash through it.
    white = QColor(255, 255, 255)
    cx, cy = size / 2, size / 2
    eye_w, eye_h = size * 0.52, size * 0.30
    p.setPen(QPen(white, max(2.0, size * 0.045)))
    p.setBrush(Qt.NoBrush)
    p.drawArc(
        QRectF(cx - eye_w / 2, cy - eye_h / 2, eye_w, eye_h), 0, 180 * 16
    )
    p.drawArc(
        QRectF(cx - eye_w / 2, cy - eye_h / 2, eye_w, eye_h), 0, -180 * 16
    )
    p.setBrush(white)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(cx - size * 0.07, cy - size * 0.07, size * 0.14, size * 0.14))
    # slash
    p.setPen(QPen(white, max(2.0, size * 0.06), Qt.SolidLine, Qt.RoundCap))
    p.drawLine(int(cx - eye_w * 0.5), int(cy + eye_h * 0.7),
               int(cx + eye_w * 0.5), int(cy - eye_h * 0.7))
    p.end()
    return pm


def app_icon() -> QIcon:
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(make_pixmap(s))
    return icon
