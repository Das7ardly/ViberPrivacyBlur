"""Persisted settings as a dataclass <-> JSON. Unknown keys are ignored so
older/newer settings files never crash the app."""

import json
from dataclasses import dataclass, asdict

from viberblur.paths import settings_path


@dataclass
class Settings:
    intensity: int = 70        # blur strength 0..100
    widget_x: int = -1         # -1 => auto-place bottom-right
    widget_y: int = -1
    widget_visible: bool = True
    start_blurred: bool = False
    blur_area: str = "chat"    # "chat" = conversation pane only, "window" = all of Viber
    region_set: bool = False   # True once the chat area has been fitted by hand
    region_left: int = 0       # chat area as insets (px) from Viber's client area
    region_top: int = 0
    region_right: int = 0
    region_bottom: int = 0


def load_settings() -> "Settings":
    s = Settings()
    try:
        with open(settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if hasattr(s, k):
                setattr(s, k, v)
    except Exception:
        pass
    return s


def save_settings(s: "Settings") -> None:
    try:
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(asdict(s), f, indent=2)
    except Exception:
        pass
