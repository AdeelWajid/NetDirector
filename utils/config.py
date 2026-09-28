import json
import os
import tempfile
from pathlib import Path

DEFAULTS = dict(theme="dark", compact=False, minimize_to_tray=True, launch_minimized=False,
                start_with_windows=False, auto_refresh=True, refresh_seconds=20,
                load_startup=True, restore_active=False, last_profile="", backend="ForceBindIP",
                forcebind_path="", bindip_path="", children=False, fallback="block",
                diagnostic_logging=False, welcomed=False)


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Settings:
    def __init__(self, root):
        self.path = Path(root) / "settings.json"
        self.values = DEFAULTS.copy()
        self.error = ""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Settings must be an object")
                for key, default in DEFAULTS.items():
                    if key in data and type(data[key]) is type(default):
                        self.values[key] = data[key]
                self.values["refresh_seconds"] = max(10, min(300, self.values["refresh_seconds"]))
                for key, choices in {"theme": {"system", "light", "dark"},
                                     "backend": {"ForceBindIP", "BindIP", "Native"},
                                     "fallback": {"block", "default", "ask", "wait"}}.items():
                    if self.values[key] not in choices:
                        self.values[key] = DEFAULTS[key]
            except (OSError, ValueError, TypeError) as exc:
                self.error = f"Could not load settings: {exc}. Defaults are in use; original file retained."

    def save(self):
        if self.error and self.path.exists():
            backup = self.path.with_suffix(".invalid.json")
            if backup.exists():
                raise ValueError("Settings recovery backup already exists; review it before saving again")
            self.path.replace(backup)
        atomic_json(self.path, self.values)
        self.error = ""

    def __getitem__(self, key):
        return self.values[key]
