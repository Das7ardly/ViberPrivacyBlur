"""Filesystem locations. Data lives in %LOCALAPPDATA%\\ViberPrivacyBlur.

VIBERBLUR_DATA_DIR overrides the data dir (used by tests). resource_path()
resolves bundled files both when running from source and when frozen by
PyInstaller (sys._MEIPASS).
"""

import os
import sys

from viberblur import APP_SLUG


def data_dir():
    override = os.environ.get("VIBERBLUR_DATA_DIR")
    base = override or os.path.join(
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
