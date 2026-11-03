"""Viber Privacy Blur — entry point.

DPI: we make the process Per-Monitor-DPI-aware v2 and turn OFF Qt's automatic
high-DPI scaling, so Qt coordinates equal physical screen pixels. That means the
overlay geometry taken from GetWindowRect lines up with Viber exactly, with no
coordinate conversion. The control widget is scaled manually for readability.
"""

import ctypes
import os
import sys


def _set_dpi_awareness():
    # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "0")
os.environ.setdefault("QT_SCALE_FACTOR", "1")
_set_dpi_awareness()

# Keep the single-instance mutex handle alive for the whole process lifetime.
_INSTANCE_MUTEX = None


def _already_running() -> bool:
    """Return True if another copy of this app already holds the named mutex."""
    global _INSTANCE_MUTEX
    ERROR_ALREADY_EXISTS = 183
    _INSTANCE_MUTEX = ctypes.windll.kernel32.CreateMutexW(
        None, False, "ViberPrivacyBlur_SingleInstance_Mutex"
    )
    return ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from viberblur import APP_NAME  # noqa: E402
from viberblur.app import Controller  # noqa: E402
from viberblur.brand import app_icon  # noqa: E402


def _selftest(app):
    """Hidden smoke test: build everything, grab a widget screenshot, exit.

    Enabled with VIBERBLUR_SELFTEST=<dir>. Runs headless-friendly bits only.
    """
    out = os.environ["VIBERBLUR_SELFTEST"]
    os.makedirs(out, exist_ok=True)
    ctrl = Controller(app)
    ctrl.widget.show()
    ctrl.widget.repaint()
    ctrl.widget.grab().save(os.path.join(out, "widget.png"))
    # exercise the blur pipeline on a synthetic image
    from PIL import Image
    from viberblur.blur import blur_to_pixmap
    img = Image.new("RGB", (400, 300), (90, 70, 200))
    pix = blur_to_pixmap(img, ctrl.settings.intensity)
    pix.save(os.path.join(out, "blur.png"))
    ctrl.overlay.set_pixmap(pix)
    ctrl.overlay.resize(400, 300)
    ctrl.overlay.repaint()
    ctrl.overlay.grab().save(os.path.join(out, "overlay.png"))
    os._exit(0)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(app_icon())

    if os.environ.get("VIBERBLUR_SELFTEST"):
        _selftest(app)

    if not sys.platform.startswith("win"):
        QMessageBox.critical(None, APP_NAME, "This app only runs on Windows.")
        return

    if _already_running():
        QMessageBox.information(
            None, APP_NAME,
            f"{APP_NAME} is already running.\n\n"
            "Look for its icon in the system tray (bottom-right).",
        )
        return

    ctrl = Controller(app)
    ctrl.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
