"""Find the Viber window and watch it move/resize/close — event-driven.

Uses SetWinEventHook scoped to Viber's process, so while blur is OFF nothing
polls and the cost is zero: the hooks simply never fire. When Viber is not
running at all, the controller falls back to a slow re-scan timer (see app.py)
that stops the moment Viber is found.
"""

import ctypes
from ctypes import wintypes

import win32gui
import win32process
from PySide6.QtCore import QObject, Signal

# WinEvent constants
WINEVENT_OUTOFCONTEXT = 0x0000
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_SYSTEM_MINIMIZESTART = 0x0016
EVENT_SYSTEM_MINIMIZEEND = 0x0017
EVENT_OBJECT_LOCATIONCHANGE = 0x800B
EVENT_OBJECT_DESTROY = 0x8001
OBJID_WINDOW = 0

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

_WinEventProc = ctypes.WINFUNCTYPE(
    None,
    wintypes.HANDLE,  # hWinEventHook
    wintypes.DWORD,   # event
    wintypes.HWND,    # hwnd
    wintypes.LONG,    # idObject
    wintypes.LONG,    # idChild
    wintypes.DWORD,   # idEventThread
    wintypes.DWORD,   # dwmsEventTime
)

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_user32.SetWinEventHook.restype = wintypes.HANDLE


def _proc_image_name(pid: int) -> str:
    h = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buf))
        if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        _kernel32.CloseHandle(h)


def find_viber_window():
    """Return (hwnd, pid) of the largest visible Viber.exe top-level window, or (None, None)."""
    best = [None, 0, None]  # hwnd, area, pid

    def _cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:
            return True
        if not _proc_image_name(pid).lower().endswith("viber.exe"):
            return True
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
        except Exception:
            return True
        area = max(0, r - l) * max(0, b - t)
        if area > best[1]:
            best[0], best[1], best[2] = hwnd, area, pid
        return True

    try:
        win32gui.EnumWindows(_cb, None)
    except Exception:
        pass
    return best[0], best[2]


class ViberTracker(QObject):
    geometryChanged = Signal()
    viberClosed = Signal()
    minimized = Signal()
    restored = Signal()
    cameToForeground = Signal()

    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.pid = None
        self._hooks = []
        self._proc = _WinEventProc(self._on_event)  # keep a reference alive

    # --- lifecycle ---------------------------------------------------------
    def bind(self) -> bool:
        """Locate Viber and install hooks. Returns True if found."""
        self.unbind()
        hwnd, pid = find_viber_window()
        if not hwnd:
            return False
        self.hwnd, self.pid = hwnd, pid
        events = (
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_MINIMIZESTART,
            EVENT_SYSTEM_MINIMIZEEND,
            EVENT_OBJECT_LOCATIONCHANGE,
            EVENT_OBJECT_DESTROY,
        )
        for event in events:
            handle = _user32.SetWinEventHook(
                event, event, 0, self._proc, pid, 0, WINEVENT_OUTOFCONTEXT
            )
            if handle:
                self._hooks.append(handle)
        return True

    def unbind(self):
        for h in self._hooks:
            try:
                _user32.UnhookWinEvent(h)
            except Exception:
                pass
        self._hooks.clear()
        self.hwnd = None
        self.pid = None

    # --- queries -----------------------------------------------------------
    def is_alive(self) -> bool:
        return bool(self.hwnd) and bool(win32gui.IsWindow(self.hwnd))

    def is_minimized(self) -> bool:
        try:
            return bool(win32gui.IsIconic(self.hwnd))
        except Exception:
            return True

    def rect(self):
        """(left, top, width, height) in physical pixels, or None."""
        try:
            l, t, r, b = win32gui.GetWindowRect(self.hwnd)
            return l, t, r - l, b - t
        except Exception:
            return None

    # --- hook callback -----------------------------------------------------
    def _on_event(self, hook, event, hwnd, id_object, id_child, thread, ts):
        if hwnd != self.hwnd or id_object != OBJID_WINDOW:
            return
        if event == EVENT_OBJECT_DESTROY:
            self.viberClosed.emit()
        elif event == EVENT_OBJECT_LOCATIONCHANGE:
            self.geometryChanged.emit()
        elif event == EVENT_SYSTEM_MINIMIZESTART:
            self.minimized.emit()
        elif event == EVENT_SYSTEM_MINIMIZEEND:
            self.restored.emit()
        elif event == EVENT_SYSTEM_FOREGROUND:
            self.cameToForeground.emit()
