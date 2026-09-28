import os
import sys
from pathlib import Path


def data_dir():
    override = os.environ.get("NETDIRECTOR_DATA_DIR") or os.environ.get("NETROUTE_DATA_DIR")
    if override:
        return Path(override)
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    current = base / "NetDirector"
    # Existing installations keep their profiles and settings after the rename.
    legacy = base / "NetRoute Pro"
    return legacy if legacy.exists() and not current.exists() else current


def asset(name):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "assets" / name
