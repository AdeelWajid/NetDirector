from abc import ABC, abstractmethod
from dataclasses import dataclass
import ctypes
import os
import shlex
import subprocess
import time


def argument_tokens(text):
    if not text.strip():
        return []
    if os.name != "nt":
        return shlex.split(text)
    count = ctypes.c_int()
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
    shell.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    pointer = shell.CommandLineToArgvW('netdirector-placeholder.exe ' + text, ctypes.byref(count))
    if not pointer:
        raise ValueError("Could not parse launch arguments")
    try:
        return [pointer[i] for i in range(1, count.value)]
    finally:
        kernel.LocalFree(pointer)


@dataclass
class LaunchResult:
    pid: int
    started: float
    backend: str
    expected_ip: str = ""
    status: str = "Launched • Windows default"
    loader: bool = False


class BindingEngine(ABC):
    name = "Abstract"
    supports_children = False
    supports_attach = False

    @abstractmethod
    def launch_application(self, rule, current_ip):
        """Receive only a freshly resolved runtime address."""

    def bind_application(self, rule, current_ip):
        return self.launch_application(rule, current_ip)

    def unbind_application(self, rule):
        return "Existing processes must be closed and relaunched to change their binding."

    def get_binding_status(self):
        return "Launch-time binding; verify live connections in Diagnostics"


def launch_default(rule):
    started = time.time()
    process = subprocess.Popen([rule.executable, *argument_tokens(rule.arguments)],
                               cwd=rule.working_directory or os.path.dirname(rule.executable) or None,
                               shell=False)
    return LaunchResult(process.pid, started, "Windows default")
