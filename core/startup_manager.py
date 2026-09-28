import os
import subprocess
import sys
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def startup_command():
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([sys.executable, "--startup"])
    interpreter = Path(sys.executable).with_name("pythonw.exe")
    return subprocess.list2cmdline([str(interpreter if interpreter.exists() else sys.executable),
                                   str(Path(__file__).resolve().parents[1] / "main.py"), "--startup"])


def set_start_with_windows(enabled):
    if os.name != "nt":
        raise RuntimeError("Windows startup registration is only available on Windows")
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, "NetDirector", 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(key, "NetDirector")
            except FileNotFoundError:
                pass
        # Retire the previous product's entry only when startup is explicitly set.
        try:
            winreg.DeleteValue(key, "NetRoutePro")
        except FileNotFoundError:
            pass
