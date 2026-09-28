from pathlib import Path
import sys

VERSION = (Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "VERSION").read_text(encoding="utf-8").strip()
