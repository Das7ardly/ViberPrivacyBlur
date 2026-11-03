"""Optional 'Start with Windows' via the per-user Run key (HKCU).

Only meaningful for the built .exe (sys.frozen). Writes a single value named
after the app; removing it fully undoes autostart. No other registry keys are
touched.
"""

import sys
import winreg

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "ViberPrivacyBlur"


def available() -> bool:
    """True when running as a built exe (a stable path to register).

    Covers PyInstaller (sys.frozen) and Nuitka (compiled module marker).
    """
    if getattr(sys, "frozen", False):
        return True
    return "__compiled__" in globals()  # set by Nuitka in every compiled module


def exe_path() -> str:
    return sys.executable


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _VALUE_NAME)
            return bool(value)
    except OSError:
        return False


def set_enabled(on: bool) -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if on:
                winreg.SetValueEx(
                    key, _VALUE_NAME, 0, winreg.REG_SZ, f'"{exe_path()}"'
                )
            else:
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
