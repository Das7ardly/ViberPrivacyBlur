"""The frosted panel shown over Viber.

Frameless, non-activating (clicks are blocked but never steal focus), and
*owned* by the Viber window via GWLP_HWNDPARENT. Ownership means Windows keeps
it directly above Viber in the z-order and hides it automatically when Viber is
minimized — so a bystander can't read or click the chat, yet the panel never
floats on top of other apps you switch to.

The panel can cover the whole Viber window or only part of it (the conversation
pane). The frost image is always of the whole window; the panel paints the
slice that lies under it, so it can be moved or resized without recapturing.
In "adjust" mode its edges can be dragged with the mouse to set that part.
"""

import ctypes

from PySide6.QtCore import Qt, QRect, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
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

ACCENT = "#7360F2"
_L, _T, _R, _B = 1, 2, 4, 8
_CURSORS = {
    _L: Qt.SizeHorCursor, _R: Qt.SizeHorCursor,
    _T: Qt.SizeVerCursor, _B: Qt.SizeVerCursor,
    _L | _T: Qt.SizeFDiagCursor, _R | _B: Qt.SizeFDiagCursor,
    _R | _T: Qt.SizeBDiagCursor, _L | _B: Qt.SizeBDiagCursor,
}


def _get_long(hwnd, idx):
    if _IS64:
        return _user32.GetWindowLongPtrW(hwnd, idx)
    return _user32.GetWindowLongW(hwnd, idx)


def _set_long(hwnd, idx, val):
    if _IS64:
        return _user32.SetWindowLongPtrW(hwnd, idx, val)
    return _user32.SetWindowLongW(hwnd, idx, val)


class Overlay(QWidget):
    regionEdited = Signal(int, int, int, int)  # x, y, w, h in screen pixels
    adjustFinished = Signal()

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
        self._origin = None   # screen (x, y) of the frost image's top-left
        self._bounds = None   # screen (x, y, w, h) the panel may be dragged within
        self._adjusting = False
        self._drag = 0        # bitmask of the edges being dragged
        self._drag_geo = None
        self._drag_pos = None
        self._hint = "Hidden  ·  press Ctrl+Alt+B to show"
        self._adjust_hint = "Drag the edges to fit the chat  ·  double-click to save"

    def set_pixmap(self, pix: QPixmap):
        self._pix = pix
        self.update()

    def place(self, left, top, width, height, origin=None, bounds=None):
        """Put the panel at a screen rect. `origin` is where the frost image's
        top-left sits on screen (the Viber window's corner); without it the
        image is stretched over the panel."""
        self._origin = origin
        self._bounds = bounds
        if self._drag:
            return  # the user is dragging an edge; don't fight them
        self.setGeometry(int(left), int(top), int(width), int(height))
        self.update()

    # --- adjust mode -------------------------------------------------------
    def is_adjusting(self) -> bool:
        return self._adjusting

    def set_adjusting(self, on: bool):
        if on == self._adjusting:
            return
        self._adjusting = on
        self._drag = 0
        self.setMouseTracking(on)
        if not on:
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def _edges_at(self, pos) -> int:
        m = int(12 * self._scale)
        edges = 0
        if pos.x() <= m:
            edges |= _L
        elif pos.x() >= self.width() - m:
            edges |= _R
        if pos.y() <= m:
            edges |= _T
        elif pos.y() >= self.height() - m:
            edges |= _B
        return edges

    def mousePressEvent(self, e):
        if self._adjusting and e.button() == Qt.LeftButton:
            self._drag = self._edges_at(e.position().toPoint())
            self._drag_geo = QRect(self.geometry())
            self._drag_pos = e.globalPosition().toPoint()
        e.accept()

    def mouseMoveEvent(self, e):
        if not self._adjusting:
            return
        if not self._drag:
            edges = self._edges_at(e.position().toPoint())
            self.setCursor(_CURSORS.get(edges, Qt.ArrowCursor))
            return
        d = e.globalPosition().toPoint() - self._drag_pos
        start = self._drag_geo
        g = QRect(start)
        m = int(120 * self._scale)  # minimum panel size
        if self._drag & _L:
            g.setLeft(min(start.left() + d.x(), start.right() - m))
        if self._drag & _R:
            g.setRight(max(start.right() + d.x(), start.left() + m))
        if self._drag & _T:
            g.setTop(min(start.top() + d.y(), start.bottom() - m))
        if self._drag & _B:
            g.setBottom(max(start.bottom() + d.y(), start.top() + m))
        if self._bounds:
            g = g.intersected(QRect(*self._bounds))
        self.setGeometry(g)
        self.update()

    def mouseReleaseEvent(self, e):
        if self._drag:
            self._drag = 0
            g = self.geometry()
            self.regionEdited.emit(g.x(), g.y(), g.width(), g.height())
        e.accept()

    def mouseDoubleClickEvent(self, e):
        if self._adjusting:
            self._drag = 0
            self.adjustFinished.emit()
        e.accept()

    # --- native window setup ----------------------------------------------
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

    # --- painting ----------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(24, 24, 30))
        if self._pix is not None:
            if self._origin is None:
                p.drawPixmap(self.rect(), self._pix)
            else:
                # Paint the slice of the whole-window frost that lies under us.
                geo = self.geometry()
                src = QRect(
                    geo.x() - self._origin[0], geo.y() - self._origin[1],
                    geo.width(), geo.height(),
                )
                part = src.intersected(self._pix.rect())
                if not part.isEmpty():
                    p.drawPixmap(part.translated(-src.x(), -src.y()), self._pix, part)

        p.setRenderHint(QPainter.Antialiasing)
        if self._adjusting:
            pen = QPen(QColor(ACCENT), max(2, int(3 * self._scale)))
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            half = pen.width() / 2
            p.drawRect(QRectF(self.rect()).adjusted(half, half, -half, -half))

        # Subtle centered hint so the blur reads as intentional, not a glitch.
        hint = self._adjust_hint if self._adjusting else self._hint
        font = QFont()
        font.setPointSizeF(11 * self._scale)
        font.setWeight(QFont.DemiBold)
        p.setFont(font)
        metrics = p.fontMetrics()
        tw = metrics.horizontalAdvance(hint)
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
        p.drawText(self.rect(), Qt.AlignCenter, hint)
