"""The control pill: a toggle button + blur-intensity slider + a minimize button.

The pill is *attached* to the Viber window (owned by it, docked to its corner,
not globally always-on-top), so it sticks to Viber, moves with it, and hides
when Viber is minimized. The minimize button tucks it away to the tray.
"""

import ctypes

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

GWL_EXSTYLE = -20
GWLP_HWNDPARENT = -8
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010

_IS64 = ctypes.sizeof(ctypes.c_void_p) == 8
_user32 = ctypes.windll.user32


def _get_long(hwnd, idx):
    return _user32.GetWindowLongPtrW(hwnd, idx) if _IS64 else _user32.GetWindowLongW(hwnd, idx)


def _set_long(hwnd, idx, val):
    return _user32.SetWindowLongPtrW(hwnd, idx, val) if _IS64 else _user32.SetWindowLongW(hwnd, idx, val)


C = {
    "bg": "#1b1b22",
    "border": "#34343f",
    "text": "#ececf2",
    "muted": "#9a9aac",
    "accent": "#7360F2",
    "accent_hi": "#8a7bf5",
    "on_accent": "#ffffff",
    "ok": "#46d17f",
}


class ControlWidget(QWidget):
    toggleRequested = Signal()
    intensityChanged = Signal(int)
    minimizeRequested = Signal()

    def __init__(self, scale: float = 1.0):
        super().__init__(
            None,
            Qt.FramelessWindowHint | Qt.Tool,  # NOT always-on-top; attached to Viber
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._scale = scale
        s = scale

        root = QVBoxLayout(self)
        root.setContentsMargins(int(12 * s), int(8 * s), int(10 * s), int(10 * s))
        root.setSpacing(int(7 * s))

        header = QHBoxLayout()
        header.setSpacing(0)
        title = QLabel("Viber Privacy")
        title.setObjectName("muted")
        tf = QFont()
        tf.setPointSizeF(8.5 * s)
        title.setFont(tf)
        self.min_btn = QPushButton("–")  # en-dash minus
        self.min_btn.setObjectName("mini")
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.setFixedSize(int(20 * s), int(20 * s))
        self.min_btn.setToolTip("Hide these controls (hotkey still works)")
        self.min_btn.clicked.connect(self.minimizeRequested)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.min_btn)
        root.addLayout(header)

        self.btn = QPushButton("Blur Viber")
        self.btn.setCursor(Qt.PointingHandCursor)
        bf = QFont()
        bf.setPointSizeF(10.5 * s)
        bf.setBold(True)
        self.btn.setFont(bf)
        self.btn.clicked.connect(self.toggleRequested)
        root.addWidget(self.btn)

        row = QHBoxLayout()
        row.setSpacing(int(8 * s))
        lbl = QLabel("Blur")
        lbl.setObjectName("muted")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setFixedWidth(int(120 * s))
        self.slider.valueChanged.connect(self._on_slider)
        self.pct = QLabel("70%")
        self.pct.setObjectName("muted")
        self.pct.setFixedWidth(int(34 * s))
        self.pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)
        row.addWidget(self.slider, 1)
        row.addWidget(self.pct)
        root.addLayout(row)

        self.setStyleSheet(self._qss(s))
        self.set_state(False, viber_found=True)

    # --- public API --------------------------------------------------------
    def set_intensity(self, value: int):
        self.slider.blockSignals(True)
        self.slider.setValue(int(value))
        self.slider.blockSignals(False)
        self.pct.setText(f"{int(value)}%")

    def set_state(self, blurred: bool, viber_found: bool = True):
        if not viber_found:
            self.btn.setText("Viber not running")
            self.btn.setProperty("state", "disabled")
        elif blurred:
            self.btn.setText("Blurred — click to show")
            self.btn.setProperty("state", "on")
        else:
            self.btn.setText("Blur Viber")
            self.btn.setProperty("state", "off")
        self.btn.style().unpolish(self.btn)
        self.btn.style().polish(self.btn)

    # --- attachment to Viber ----------------------------------------------
    def attach_to(self, owner_hwnd: int):
        """Own the pill to Viber and drop its global always-on-top flag."""
        hwnd = int(self.winId())
        ex = _get_long(hwnd, GWL_EXSTYLE)
        _set_long(hwnd, GWL_EXSTYLE, (ex | WS_EX_TOOLWINDOW) & ~WS_EX_TOPMOST)
        if owner_hwnd:
            _set_long(hwnd, GWLP_HWNDPARENT, int(owner_hwnd))
        _user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def detach(self):
        """No Viber: clear owner and float on top so the user can still see it."""
        hwnd = int(self.winId())
        _set_long(hwnd, GWLP_HWNDPARENT, 0)
        _user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def raise_self(self):
        """Lift above the frost overlay without stealing focus."""
        try:
            _user32.SetWindowPos(int(self.winId()), HWND_TOP, 0, 0, 0, 0,
                                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        except Exception:
            pass

    # --- internal ----------------------------------------------------------
    def _on_slider(self, value):
        self.pct.setText(f"{value}%")
        self.intensityChanged.emit(int(value))

    def _qss(self, s):
        return f"""
        QWidget {{ color: {C['text']}; font-family: 'Segoe UI'; }}
        ControlWidget {{ background: transparent; }}
        QLabel#muted {{ color: {C['muted']}; }}
        QPushButton {{
            background: {C['accent']}; color: {C['on_accent']};
            border: none; border-radius: {int(9*s)}px;
            padding: {int(9*s)}px {int(14*s)}px;
        }}
        QPushButton:hover {{ background: {C['accent_hi']}; }}
        QPushButton[state="on"] {{ background: {C['ok']}; color: #10110f; }}
        QPushButton[state="disabled"] {{ background: #3a3a44; color: {C['muted']}; }}
        QPushButton#mini {{
            background: transparent; color: {C['muted']};
            border: none; border-radius: {int(5*s)}px; padding: 0;
            font-size: {int(14*s)}px; font-weight: bold;
        }}
        QPushButton#mini:hover {{ background: {C['border']}; color: {C['text']}; }}
        QSlider::groove:horizontal {{
            height: {int(6*s)}px; border-radius: {int(3*s)}px; background: {C['border']};
        }}
        QSlider::sub-page:horizontal {{
            height: {int(6*s)}px; border-radius: {int(3*s)}px; background: {C['accent']};
        }}
        QSlider::handle:horizontal {{
            width: {int(14*s)}px; height: {int(14*s)}px; margin: -{int(5*s)}px 0;
            border-radius: {int(7*s)}px; background: {C['text']};
        }}
        """

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = int(14 * self._scale)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(C["bg"]))
        p.drawRoundedRect(r, radius, radius)
        p.setPen(QPen(QColor(C["border"]), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r, radius, radius)
