"""Capture window pixels into a PIL image.

Two paths:
- capture_window(): PrintWindow with PW_RENDERFULLCONTENT. Grabs the target
  window's own content even if another window (our overlay) sits on top, so
  recapturing while blurred never reveals the chat and never feeds the blur
  back into itself. Some GPU-accelerated windows return black here.
- capture_rect(): straight screen BitBlt of a screen rectangle. Accurate for
  whatever is actually on screen; used for the first blur (overlay not shown
  yet) and as the fallback when PrintWindow comes back black.
"""

import ctypes

import win32con
import win32gui
import win32ui
from PIL import Image, ImageStat

PW_RENDERFULLCONTENT = 0x00000002


def _bitmap_to_image(bmp):
    info = bmp.GetInfo()
    bits = bmp.GetBitmapBits(True)
    return Image.frombuffer(
        "RGB", (info["bmWidth"], info["bmHeight"]), bits, "raw", "BGRX", 0, 1
    )


def _looks_black(img) -> bool:
    try:
        small = img.resize((16, 16)).convert("L")
        return ImageStat.Stat(small).mean[0] < 4.0
    except Exception:
        return False


def capture_rect(left, top, width, height):
    """BitBlt a rectangle of the virtual screen."""
    if width <= 0 or height <= 0:
        return None
    desktop = win32gui.GetDesktopWindow()
    screen_dc = win32gui.GetWindowDC(desktop)
    srcdc = win32ui.CreateDCFromHandle(screen_dc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    try:
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)
        return _bitmap_to_image(bmp)
    except Exception:
        return None
    finally:
        _cleanup(bmp, memdc, srcdc, desktop, screen_dc)


def capture_window(hwnd):
    """PrintWindow the given window; returns None if it renders black/empty."""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    except Exception:
        return None
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0:
        return None
    window_dc = win32gui.GetWindowDC(hwnd)
    srcdc = win32ui.CreateDCFromHandle(window_dc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    try:
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        ok = ctypes.windll.user32.PrintWindow(
            hwnd, memdc.GetSafeHdc(), PW_RENDERFULLCONTENT
        )
        if not ok:
            return None
        img = _bitmap_to_image(bmp)
        return None if _looks_black(img) else img
    except Exception:
        return None
    finally:
        _cleanup(bmp, memdc, srcdc, hwnd, window_dc)


def _cleanup(bmp, memdc, srcdc, hwnd, dc):
    try:
        win32gui.DeleteObject(bmp.GetHandle())
    except Exception:
        pass
    try:
        memdc.DeleteDC()
    except Exception:
        pass
    try:
        srcdc.DeleteDC()
    except Exception:
        pass
    try:
        win32gui.ReleaseDC(hwnd, dc)
    except Exception:
        pass
