import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
import ipaddress
from bindings.base_engine import BindingEngine, LaunchResult, argument_tokens


def executable_architecture(executable):
    with open(executable, "rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("The selected file is not a Windows executable")
        stream.seek(0x3C)
        offset = struct.unpack("<I", stream.read(4))[0]
        stream.seek(offset)
        if stream.read(4) != b"PE\0\0":
            raise ValueError("Invalid Windows executable header")
        machine = struct.unpack("<H", stream.read(2))[0]
    if machine not in (0x14C, 0x8664):
        raise ValueError("ForceBindIP supports x86 and x64 targets; this executable has another architecture")
    return "x64" if machine == 0x8664 else "x86"


def detect_directories():
    candidates = []
    app_root = Path(getattr(sys, "_MEIPASS", sys.executable)).resolve().parent
    project_root = Path(__file__).resolve().parents[1]
    for base in (app_root, project_root):
        candidates.extend([base, base / "ForceBindIP", base / "build" / "ForceBindIP"])
    for exe in ("ForceBindIP.exe", "ForceBindIP64.exe"):
        located = shutil.which(exe)
        if located:
            candidates.append(Path(located).parent)
    for variable in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        root = os.environ.get(variable)
        if root:
            candidates.append(Path(root) / "ForceBindIP")
    return candidates


class ForceBindEngine(BindingEngine):
    name = "ForceBindIP"

    def __init__(self, directory=""):
        self.directory = directory

    def backend_for(self, executable):
        arch = executable_architecture(executable)
        filename = "ForceBindIP64.exe" if arch == "x64" else "ForceBindIP.exe"
        dll = "BindIP64.dll" if arch == "x64" else "BindIP.dll"
        candidates = [Path(self.directory)] if self.directory else detect_directories()
        for folder in candidates:
            if folder.is_file():
                folder = folder.parent
            if (folder / filename).is_file() and (folder / dll).is_file():
                return folder / filename
        raise FileNotFoundError(f"ForceBindIP {arch} is unavailable. Select a directory containing {filename} and {dll} in Settings.")

    def build_command(self, rule, current_ip):
        ipaddress.IPv4Address(current_ip)
        return [str(self.backend_for(rule.executable)), current_ip, rule.executable, *argument_tokens(rule.arguments)]

    def launch_application(self, rule, current_ip):
        command = self.build_command(rule, current_ip)
        started = time.time()
        process = subprocess.Popen(command, cwd=rule.working_directory or str(Path(rule.executable).parent),
                                   shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            result = process.wait(timeout=0.35)
            if result != 0:
                raise RuntimeError(f"ForceBindIP failed (exit {result}). Check the backend installation and target compatibility.")
        except subprocess.TimeoutExpired:
            pass
        return LaunchResult(process.pid, started, self.name, current_ip, "Binding requested • unverified", True)
