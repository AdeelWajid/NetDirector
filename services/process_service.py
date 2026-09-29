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


def list_running_applications(include_system=False):
    """Enumerate running applications deduplicated by executable path."""
    import ctypes
    from ctypes import wintypes
    user32 = getattr(ctypes, "windll", None)
    titles = {}
    if user32 and hasattr(user32, "user32"):
        u32 = user32.user32
        def enum_proc(hwnd, _):
            if u32.IsWindowVisible(hwnd):
                length = u32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    u32.GetWindowTextW(hwnd, buff, length + 1)
                    t = buff.value.strip()
                    if t:
                        pid = wintypes.DWORD()
                        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        if pid.value and pid.value not in titles:
                            titles[pid.value] = t
            return True
        wnd_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        try:
            u32.EnumWindows(wnd_proc(enum_proc), 0)
        except Exception:
            pass

    apps = {}
    win_dir = os.path.normcase(os.environ.get("SystemRoot", r"C:\Windows"))
    for p in psutil.process_iter(["pid", "name", "exe"]):
        try:
            info = p.info
            exe = info["exe"]
            if not exe or not Path(exe).is_file():
                continue
            norm_exe = os.path.normcase(exe)
            is_system = norm_exe.startswith(win_dir)
            if not include_system and is_system:
                continue
            title = titles.get(info["pid"], "")
            if norm_exe not in apps or (title and not apps[norm_exe]["title"]):
                apps[norm_exe] = {
                    "pid": info["pid"],
                    "name": Path(exe).stem,
                    "exe": str(Path(exe).resolve()),
                    "title": title,
                    "is_system": is_system
                }
        except (psutil.Error, OSError):
            continue
    return sorted(apps.values(), key=lambda a: (not bool(a["title"]), a["name"].lower()))


def discover_installed_games():
    """Discover installed games from Steam, Epic Games, and other standard libraries."""
    import re
    import json
    games = []
    # 1. Steam Games
    candidates = []
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                candidates.append(Path(winreg.QueryValueEx(key, "SteamPath")[0]))
        except OSError:
            pass
    for v in ("ProgramFiles(x86)", "ProgramFiles"):
        if os.environ.get(v):
            candidates.append(Path(os.environ[v]) / "Steam")
    steam_root = next((p for p in candidates if p.is_dir()), None)
    if steam_root:
        library_folders = [steam_root / "steamapps"]
        vdf = steam_root / "steamapps" / "libraryfolders.vdf"
        if vdf.is_file():
            try:
                text = vdf.read_text(encoding="utf-8", errors="ignore")
                for match in re.finditer(r'"path"\s+"([^"]+)"', text):
                    p = Path(match.group(1).replace(r"\\", "\\")) / "steamapps"
                    if p.is_dir() and p not in library_folders:
                        library_folders.append(p)
            except Exception:
                pass
        for lib in library_folders:
            for acf in lib.glob("appmanifest_*.acf"):
                try:
                    content = acf.read_text(encoding="utf-8", errors="ignore")
                    name_m = re.search(r'"name"\s+"([^"]+)"', content)
                    install_m = re.search(r'"installdir"\s+"([^"]+)"', content)
                    if not name_m or not install_m:
                        continue
                    game_name = name_m.group(1)
                    if "redistributable" in game_name.lower() or "steamworks" in game_name.lower():
                        continue
                    common_dir = lib / "common" / install_m.group(1)
                    if not common_dir.is_dir():
                        continue
                    exes = [e for e in common_dir.rglob("*.exe")
                            if not any(skip in e.name.lower() for skip in ["crash", "report", "unins", "setup", "redist", "unitycrash", "dxsetup", "easyanticheat"])]
                    best_exe = None
                    for e in exes:
                        if e.stem.lower() in (install_m.group(1).lower(), game_name.lower().replace(" ", "")):
                            best_exe = str(e.resolve())
                            break
                    if not best_exe and exes:
                        best_exe = str(exes[0].resolve())
                    if best_exe:
                        games.append({"name": game_name, "launcher": "Steam", "executable": best_exe})
                except Exception:
                    continue

    # 2. Epic Games
    manifests = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests")
    if manifests.is_dir():
        for item_file in manifests.glob("*.item"):
            try:
                data = json.loads(item_file.read_text(encoding="utf-8", errors="ignore"))
                name = data.get("DisplayName")
                install_loc = data.get("InstallLocation")
                launch_exe = data.get("LaunchExecutable")
                if name and install_loc and launch_exe:
                    exe_path = Path(install_loc) / launch_exe
                    if exe_path.is_file():
                        games.append({"name": name, "launcher": "Epic Games", "executable": str(exe_path.resolve())})
            except Exception:
                continue

    return sorted(games, key=lambda g: g["name"].lower())
