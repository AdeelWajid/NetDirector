import os
from pathlib import Path
import psutil


def normalized(path):
    return os.path.normcase(os.path.abspath(path))


def matching_processes(executable, since=0):
    target = normalized(executable)
    result = []
    for process in psutil.process_iter(["pid", "exe", "create_time", "name"]):
        try:
            info = process.info
            if info["exe"] and normalized(info["exe"]) == target and (info["create_time"] or 0) >= since:
                result.append(process)
        except (psutil.Error, OSError):
            continue
    return result


def steam_path():
    candidates = []
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                candidates.append(Path(winreg.QueryValueEx(key, "SteamPath")[0]) / "steam.exe")
        except OSError:
            pass
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        if os.environ.get(variable):
            candidates.append(Path(os.environ[variable]) / "Steam" / "steam.exe")
    return next((str(p) for p in candidates if p.is_file()), "")
