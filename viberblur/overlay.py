"""The frosted panel shown over Viber.

Frameless, non-activating (clicks are blocked but never steal focus), and
*owned* by the Viber window via GWLP_HWNDPARENT. Ownership means Windows keeps
it directly above Viber in the z-order and hides it automatically when Viber is
minimized — so a bystander can't read or click the chat, yet the panel never
floats on top of other apps you switch to.
"""

import ctypes

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

GWL_EXSTYLE = -20
GWLP_HWNDPARENT = -8
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

HWND_TOP = 0
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010

_IS64 = ctypes.sizeof(ctypes.c_void_p) == 8
_user32 = ctypes.windll.user32


def _get_long(hwnd, idx):
    if _IS64:
        return _user32.GetWindowLongPtrW(hwnd, idx)
    return _user32.GetWindowLongW(hwnd, idx)


def _set_long(hwnd, idx, val):
    if _IS64:
        return _user32.SetWindowLongPtrW(hwnd, idx, val)
    return _user32.SetWindowLongW(hwnd, idx, val)


class Overlay(QWidget):
    def __init__(self, scale: float = 1.0):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setCursor(Qt.ArrowCursor)
        self._scale = scale
        self._pix = None
        self._hint = "Hidden  ·  press Ctrl+Alt+B to show"

    def set_pixmap(self, pix: QPixmap):
        self._pix = pix
        self.update()

    def place(self, left, top, width, height):
        self.setGeometry(int(left), int(top), int(width), int(height))

    def apply_native_styles(self, owner_hwnd):
        """Make the window non-activating and owned by Viber. Call after show()."""
        hwnd = int(self.winId())
        ex = _get_long(hwnd, GWL_EXSTYLE)
        _set_long(hwnd, GWL_EXSTYLE, ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        if owner_hwnd:
            _set_long(hwnd, GWLP_HWNDPARENT, int(owner_hwnd))

    def raise_above(self, owner_hwnd):
        """Lift the overlay to the top of its z-order band so it sits over Viber
        without stealing focus."""
        try:
            _user32.SetWindowPos(
                int(self.winId()), HWND_TOP, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def paintEvent(self, _event):
        p = QPainter(self)
        if self._pix is not None:
            p.drawPixmap(self.rect(), self._pix)
        else:
            p.fillRect(self.rect(), QColor(24, 24, 30))
        # Subtle centered hint so the blur reads as intentional, not a glitch.
        p.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setPointSizeF(11 * self._scale)
        font.setWeight(QFont.DemiBold)
        p.setFont(font)
        metrics = p.fontMetrics()
        tw = metrics.horizontalAdvance(self._hint)
        th = metrics.height()
        pad = 16
        chip = QRectF(
            (self.width() - tw) / 2 - pad,
            (self.height() - th) / 2 - pad / 2,
            tw + pad * 2,
            th + pad,
        )
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawRoundedRect(chip, 10, 10)
        p.setPen(QColor(255, 255, 255, 220))
        p.drawText(self.rect(), Qt.AlignCenter, self._hint)
