"""Read-only Windows networking discovery, isolated from the Qt event thread."""
import json
import os
import subprocess
import ipaddress
from models.adapter import Adapter, AdapterIdentity

SCRIPT = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$addresses = @(Get-NetIPAddress -ErrorAction Stop)
$dns = @(Get-DnsClientServerAddress -ErrorAction Stop)
$routes = @(Get-NetRoute -ErrorAction Stop | Where-Object { $_.DestinationPrefix -in @('0.0.0.0/0','::/0') })
$result = @(Get-NetAdapter -IncludeHidden -ErrorAction Stop | ForEach-Object {
    $a = $_
    [pscustomobject]@{
        name = $a.Name; description = $a.InterfaceDescription
        guid = [string]$a.InterfaceGuid; index = [int]$a.ifIndex
        mac = $a.MacAddress; status = [string]$a.Status
        kind = [string]$a.PhysicalMediaType; link_speed = [string]$a.LinkSpeed
        ipv4 = @($addresses | Where-Object { $_.InterfaceIndex -eq $a.ifIndex -and $_.AddressFamily -eq 'IPv4' -and $_.AddressState -eq 'Preferred' -and -not $_.SkipAsSource } | ForEach-Object IPAddress)
        ipv6 = @($addresses | Where-Object { $_.InterfaceIndex -eq $a.ifIndex -and $_.AddressFamily -eq 'IPv6' -and $_.AddressState -eq 'Preferred' } | ForEach-Object IPAddress)
        gateways = @($routes | Where-Object { $_.InterfaceIndex -eq $a.ifIndex } | ForEach-Object NextHop)
        dns = @($dns | Where-Object { $_.InterfaceIndex -eq $a.ifIndex } | ForEach-Object ServerAddresses)
    }
})
ConvertTo-Json -InputObject $result -Depth 5 -Compress
'''


import socket
import re


def get_connected_wifi_ssid():
    """Extract the currently connected Wi-Fi SSID if available."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        out = subprocess.check_output(["netsh", "wlan", "show", "interfaces"],
                                      encoding="utf-8", errors="ignore",
                                      creationflags=flags)
        match = re.search(r"^\s*SSID\s*:\s*(.+)$", out, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return ""


def check_adapter_internet(ip, timeout=0.8):
    """Test outbound internet reachability through a specific local IP."""
    if not ip:
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.bind((ip, 0))
        s.connect(("1.1.1.1", 53))
        s.send(b"\x00")
        s.close()
        return True
    except Exception:
        return False


def parse_adapters(raw):
    rows = json.loads(raw.lstrip("\ufeff"))
    if isinstance(rows, dict):
        rows = [rows]
    result = []
    for row in rows or []:
        identity = AdapterIdentity(**{k: row.get(k) or (0 if k == "index" else "")
                                      for k in AdapterIdentity.__dataclass_fields__})
        ipv4 = [ip for ip in row.get("ipv4", []) if not ipaddress.ip_address(ip).is_link_local
                and not ipaddress.ip_address(ip).is_loopback]
        status = row.get("status") or "Unknown"
        has_internet = False
        if ipv4 and status.lower() == "up":
            has_internet = check_adapter_internet(ipv4[0])
        result.append(Adapter(identity, ipv4, row.get("ipv6") or [], row.get("gateways") or [],
                              row.get("dns") or [], status,
                              row.get("kind") or "Virtual / other", row.get("link_speed") or "",
                              has_internet=has_internet))
    return result


def discover_adapters():
    if os.name != "nt":
        raise RuntimeError("Adapter discovery requires Windows 10 or Windows 11")
    windows = os.environ.get("SystemRoot", r"C:\Windows")
    # A 32-bit process on 64-bit Windows needs Sysnative to reach NetAdapter's
    # native PowerShell modules; System32 would be redirected to SysWOW64.
    native = "Sysnative" if os.path.isdir(os.path.join(windows, "Sysnative")) else "System32"
    powershell = os.path.join(windows, native, "WindowsPowerShell", "v1.0", "powershell.exe")
    result = subprocess.run([powershell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", SCRIPT],
                            capture_output=True, encoding="utf-8", errors="replace", timeout=40,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError("Windows could not enumerate adapters. " + result.stderr.strip()[:400])
    return parse_adapters(result.stdout)
