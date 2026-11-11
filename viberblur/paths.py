"""Filesystem locations.

Installed copy: data lives in %LOCALAPPDATA%\\ViberPrivacyBlur.
Portable copy: if a file named portable.txt sits next to the exe, data lives in
a "data" folder beside it, so the whole folder can be carried on a USB stick
and nothing is written to the user profile.

VIBERBLUR_DATA_DIR overrides the data dir (used by tests). resource_path()
resolves bundled files both when running from source and when frozen by
PyInstaller (sys._MEIPASS).
"""

import os
import sys

from viberblur import APP_SLUG


def app_dir():
    """Folder holding the exe (or the project root when run from source)."""
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_portable():
    return os.path.exists(os.path.join(app_dir(), "portable.txt"))


def data_dir():
    override = os.environ.get("VIBERBLUR_DATA_DIR")
    if override:
        base = override
    elif is_portable():
        base = os.path.join(app_dir(), "data")
    else:
        base = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_SLUG
        )
    os.makedirs(base, exist_ok=True)
    return base


def settings_path():
    return os.path.join(data_dir(), "settings.json")


def resource_path(rel):
    base = getattr(
        sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(base, rel)
