"""Global hotkey via RegisterHotKey + a Qt native event filter.

RegisterHotKey posts WM_HOTKEY to the owning window's message queue; the filter
catches it. This is event-driven and costs nothing when idle.
"""

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

_user32 = ctypes.windll.user32


class HotkeyManager(QAbstractNativeEventFilter):
    def __init__(self, hwnd: int, hotkey_id: int, callback):
        super().__init__()
        self._hwnd = int(hwnd)
        self._id = hotkey_id
        self._callback = callback
        self._registered = False

    def register(self, mods: int, vk: int) -> bool:
        self.unregister()
        ok = bool(
            _user32.RegisterHotKey(self._hwnd, self._id, mods | MOD_NOREPEAT, vk)
        )
        self._registered = ok
        return ok

    def unregister(self):
        if self._registered:
            try:
                _user32.UnregisterHotKey(self._hwnd, self._id)
            except Exception:
                pass
            self._registered = False

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG" or event_type == "windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == self._id:
                self._callback()
        return False, 0
