"""Controller: wires the tracker, overlay, control widget, tray and hotkey.

Performance contract: while blur is OFF nothing runs but two event hooks (which
only fire when Viber actually moves/closes). No timers spin in the background.
The only timers are short, single-shot debouncers used *during* a blur, and a
slow re-scan that runs *only* while Viber is not running.
"""

import ctypes
import os
import time

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from viberblur import APP_NAME
from viberblur import autostart
from viberblur.blur import blur_to_pixmap
from viberblur.brand import app_icon
from viberblur.capture import capture_rect, capture_window
from viberblur.hotkey import HotkeyManager, MOD_ALT, MOD_CONTROL
from viberblur.overlay import Overlay
from viberblur.settings import load_settings, save_settings
from viberblur.widget import ControlWidget
from viberblur.window_tracker import ViberTracker

HOTKEY_ID = 0xB102
HOTKEY_VK = 0x42  # 'B'
HOTKEY_MODS = MOD_CONTROL | MOD_ALT
HOTKEY_LABEL = "Ctrl+Alt+B"


def _dbg(msg: str):
    path = os.environ.get("VIBERBLUR_DEBUG")
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass


def _ui_scale() -> float:
    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        return max(1.0, min(3.0, dpi / 96.0))
    except Exception:
        return 1.0


class Controller:
    def __init__(self, app: QApplication):
        self.app = app
        self.settings = load_settings()
        self.scale = _ui_scale()
        self.blurred = False
        self._last_size = None
        self._last_toggle = 0.0

        self.tracker = ViberTracker()
        self.overlay = Overlay(scale=self.scale)
        self.widget = ControlWidget(scale=self.scale)
        self.widget.set_intensity(self.settings.intensity)

        # Debouncers (single-shot, created stopped — zero idle cost).
        self._recap_timer = QTimer()
        self._recap_timer.setSingleShot(True)
        self._recap_timer.timeout.connect(self._recapture)
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(lambda: save_settings(self.settings))
        self._rescan = QTimer()
        self._rescan.setInterval(2000)
        self._rescan.timeout.connect(self._rescan_tick)

        # The hotkey lives on its own hidden window that never moves, hides, or
        # re-parents — so it keeps working no matter what Viber or the pill do
        # (e.g. while Viber is minimized).
        self._hk_host = QWidget()
        self._hk_host.setWindowFlag(Qt.Tool, True)
        self._hk_host.resize(0, 0)
        self._hk_host.setAttribute(Qt.WA_DontShowOnScreen, True)
        _ = self._hk_host.winId()  # realize the native handle
        self.hotkey = HotkeyManager(int(self._hk_host.winId()), HOTKEY_ID, self.toggle_blur)

        self._tray = None
        self._connect_signals()

    # --- startup -----------------------------------------------------------
    def start(self):
        found = self.tracker.bind()
        self.widget.set_state(False, viber_found=found)
        self._reposition_widget()
        self.app.installNativeEventFilter(self.hotkey)
        hk_ok = self.hotkey.register(HOTKEY_MODS, HOTKEY_VK)
        _dbg(f"start: hotkey_register={bool(hk_ok)} host_hwnd={int(self._hk_host.winId())} pid={os.getpid()}")
        self._build_tray()
        if not hk_ok and self._tray:
            self._tray.showMessage(
                APP_NAME,
                f"Couldn't register {HOTKEY_LABEL} (another app may use it). "
                "Use the pill or tray icon to blur.",
                QSystemTrayIcon.Warning,
                5000,
            )
        if not found:
            self._rescan.start()
        elif self.settings.start_blurred:
            self.apply_blur()

    def _connect_signals(self):
        self.tracker.geometryChanged.connect(self._on_geometry_changed)
        self.tracker.viberClosed.connect(self._on_viber_closed)
        self.tracker.minimized.connect(self._on_minimized)
        self.tracker.restored.connect(self._on_restored)
        self.tracker.cameToForeground.connect(self._on_foreground)
        self.widget.toggleRequested.connect(self.toggle_blur)
        self.widget.intensityChanged.connect(self._on_intensity)
        self.widget.minimizeRequested.connect(self._minimize_widget)

    # --- blur control ------------------------------------------------------
    def toggle_blur(self):
        _dbg(f"toggle_blur called t={time.monotonic():.3f} currently_blurred={self.blurred}")
        now = time.monotonic()
        if now - self._last_toggle < 0.25:  # ignore accidental double-fire
            return
        self._last_toggle = now
        if self.blurred:
            self.clear_blur()
        else:
            self.apply_blur()

    def apply_blur(self):
        if not self.tracker.is_alive():
            if not self.tracker.bind():
                self.widget.set_state(False, viber_found=False)
                self._rescan.start()
                return
        self.blurred = True
        self.widget.set_state(True, viber_found=True)
        self._update_tray()
        if self.tracker.is_minimized():
            # Viber is minimized: show nothing now; the overlay appears the
            # moment Viber is restored (it is attached to Viber's state).
            self.overlay.hide()
        else:
            self._render_overlay()

    def clear_blur(self):
        self.overlay.hide()
        self.blurred = False
        self.widget.set_state(False, viber_found=self.tracker.is_alive())
        self._update_tray()

    def _render_overlay(self):
        """Capture Viber, frost it, and lock the overlay over the window."""
        if not self.tracker.is_alive():
            return
        r = self.tracker.rect()
        if not r:
            return
        left, top, w, h = r
        if self.overlay.isVisible():
            # Overlay already covers Viber: PrintWindow reads Viber's own pixels,
            # so we never capture the blur itself. Fall back to a hidden grab.
            img = capture_window(self.tracker.hwnd)
            if img is None:
                self.overlay.hide()
                img = capture_rect(left, top, w, h)
        else:
            img = capture_rect(left, top, w, h) or capture_window(self.tracker.hwnd)
        if img is None:
            return
        self.overlay.set_pixmap(blur_to_pixmap(img, self.settings.intensity))
        self.overlay.place(left, top, w, h)
        self.overlay.show()
        self.overlay.apply_native_styles(self.tracker.hwnd)
        self.overlay.raise_above(self.tracker.hwnd)
        self._last_size = (w, h)
        # Keep the pill above the frost so the controls stay reachable.
        if self.settings.widget_visible and not self.tracker.is_minimized():
            self.widget.raise_self()

    def _recapture(self):
        """Refresh the frosted image in place (after resize or intensity change)."""
        if not self.blurred or self.tracker.is_minimized():
            return
        self._render_overlay()

    # --- tracker events ----------------------------------------------------
    def _on_geometry_changed(self):
        if self.tracker.is_minimized():
            self.overlay.hide()
            self.widget.hide()
            return
        r = self.tracker.rect()
        if not r:
            return
        left, top, w, h = r
        if self.blurred:
            self.overlay.place(left, top, w, h)  # move with Viber immediately
            if (w, h) != self._last_size:
                self._last_size = (w, h)
                self._recap_timer.start(120)  # debounce recapture during resize
        self._dock_widget_position()  # the pill sticks to Viber's corner

    def _on_minimized(self):
        self.overlay.hide()
        self.widget.hide()  # the pill goes away with Viber

    def _on_restored(self):
        if self.blurred:
            self._render_overlay()  # come back up with Viber
        self._reposition_widget()

    def _on_foreground(self):
        if self.tracker.is_minimized():
            return
        if self.blurred:
            self._render_overlay()  # re-assert the frost above Viber
        self._reposition_widget()

    def _on_viber_closed(self):
        self.clear_blur()
        self.tracker.unbind()
        self.widget.set_state(False, viber_found=False)
        self._reposition_widget()  # detach, float at screen corner
        self._update_tray()
        self._rescan.start()

    def _rescan_tick(self):
        if self.tracker.bind():
            self._rescan.stop()
            self.widget.set_state(self.blurred, viber_found=True)
            self._reposition_widget()
            self._update_tray()

    # --- widget placement / settings --------------------------------------
    def _on_intensity(self, value):
        self.settings.intensity = int(value)
        self._save_timer.start(400)
        if self.blurred:
            self._recap_timer.start(60)

    def _minimize_widget(self):
        self.settings.widget_visible = False
        self.widget.hide()
        self._save_timer.start(200)
        self._update_tray()

    def _docked_point(self, r):
        """Top-center of the Viber window, just below its top edge."""
        left, top, w, _h = r
        m = int(12 * self.scale)
        x = left + (w - self.widget.width()) // 2
        y = top + m
        return x, y

    def _dock_widget_position(self):
        """Move the pill to Viber's top-center (no show/attach)."""
        if not self.settings.widget_visible or not self.widget.isVisible():
            return
        if not self.tracker.is_alive() or self.tracker.is_minimized():
            return
        r = self.tracker.rect()
        if not r:
            return
        self.widget.adjustSize()
        self.widget.move(*self._docked_point(r))

    def _reposition_widget(self):
        """Full placement: dock+attach to Viber, or float at the screen corner."""
        if not self.settings.widget_visible:
            self.widget.hide()
            return
        self.widget.adjustSize()
        if self.tracker.is_alive():
            if self.tracker.is_minimized():
                self.widget.hide()
                return
            r = self.tracker.rect()
            if r:
                self.widget.move(*self._docked_point(r))
            self.widget.show()
            self.widget.attach_to(self.tracker.hwnd)  # owned by Viber, not top-of-all
            self.widget.raise_self()
        else:
            screen = self.app.primaryScreen().availableGeometry()
            m = int(24 * self.scale)
            self.widget.move(
                screen.right() - self.widget.width() - m,
                screen.bottom() - self.widget.height() - m,
            )
            self.widget.show()
            self.widget.detach()  # no Viber: keep it visible on top

    # --- tray --------------------------------------------------------------
    def _build_tray(self):
        self._tray = QSystemTrayIcon(app_icon(), self.app)
        self._tray.setToolTip(APP_NAME)
        menu = QMenu()
        self._act_toggle = QAction(f"Blur / show  ({HOTKEY_LABEL})", menu)
        self._act_toggle.triggered.connect(self.toggle_blur)
        self._act_widget = QAction("Hide controls", menu)
        self._act_widget.triggered.connect(self._toggle_widget)
        menu.addAction(self._act_toggle)
        menu.addAction(self._act_widget)
        if autostart.available():
            menu.addSeparator()
            self._act_autostart = QAction("Start with Windows", menu)
            self._act_autostart.setCheckable(True)
            self._act_autostart.setChecked(autostart.is_enabled())
            self._act_autostart.toggled.connect(lambda on: autostart.set_enabled(bool(on)))
            menu.addAction(self._act_autostart)
        menu.addSeparator()
        act_quit = QAction("Quit", menu)
        act_quit.triggered.connect(self.quit)
        menu.addAction(act_quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()
        self._update_tray()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_blur()

    def _toggle_widget(self):
        if self.widget.isVisible():
            self.settings.widget_visible = False
            self.widget.hide()
        else:
            self.settings.widget_visible = True
            self._reposition_widget()
        self._save_timer.start(200)
        self._update_tray()

    def _update_tray(self):
        if not self._tray:
            return
        self._act_widget.setText(
            "Hide controls" if self.widget.isVisible() else "Show controls"
        )
        state = "Blurred" if self.blurred else "Visible"
        self._tray.setToolTip(f"{APP_NAME} — {state}")

    # --- shutdown ----------------------------------------------------------
    def quit(self):
        self.hotkey.unregister()
        self.tracker.unbind()
        save_settings(self.settings)
        if self._tray:
            self._tray.hide()
        self.app.quit()
