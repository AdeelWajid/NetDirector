"""Download, verify, and extract ForceBindIP binaries for packaging."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FORCEBINDIP_URL = "https://r1ch.net/assets/forcebindip/ForceBindIP-1.32-Setup.exe"
FORCEBINDIP_SHA256 = "bda0ee4a3843410a57fc5ab6ee6c87de2242048483ab1e1410a4a61801ede9f3"
REQUIRED_FILES = ("ForceBindIP.exe", "ForceBindIP64.exe", "BindIP.dll", "BindIP64.dll")


def find_7z():
    candidates = [
        shutil.which("7z"),
        shutil.which("7za"),
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
        Path(os.environ.get("TEMP", "")) / "my7zip" / "Files" / "7-Zip" / "7z.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "7-Zip" / "7z.exe",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c)
    return None


def ensure_7z(work_dir: Path) -> Path:
    found = find_7z()
    if found:
        return found
    msi_url = "https://www.7-zip.org/a/7z2408-x64.msi"
    msi_path = work_dir / "7z.msi"
    unpack_dir = work_dir / "7zip_extracted"
    print("Downloading 7-Zip for NSIS extraction...")
    urllib.request.urlretrieve(msi_url, msi_path)
    subprocess.run(["msiexec.exe", "/a", str(msi_path), "/qn", f"TARGETDIR={unpack_dir}"], check=True)
    exe = unpack_dir / "Files" / "7-Zip" / "7z.exe"
    if not exe.is_file():
        raise RuntimeError("Failed to extract 7-Zip")
    return exe


def fetch_forcebindip(output_dir: Path = None) -> Path:
    if output_dir is None:
        output_dir = ROOT / "build" / "ForceBindIP"
    output_dir.mkdir(parents=True, exist_ok=True)

    if all((output_dir / f).is_file() for f in REQUIRED_FILES):
        print(f"ForceBindIP binaries already present in {output_dir}")
        return output_dir

    work_dir = ROOT / "build" / "temp_fbind"
    work_dir.mkdir(parents=True, exist_ok=True)

    installer_file = work_dir / "ForceBindIP-Setup.exe"
    if not installer_file.is_file():
        print(f"Downloading ForceBindIP from {FORCEBINDIP_URL}...")
        urllib.request.urlretrieve(FORCEBINDIP_URL, installer_file)

    data = installer_file.read_bytes()
    digest = hashlib.sha256(data).hexdigest().lower()
    if digest != FORCEBINDIP_SHA256:
        installer_file.unlink(missing_ok=True)
        raise ValueError(f"Checksum mismatch for ForceBindIP: got {digest}, expected {FORCEBINDIP_SHA256}")

    print("ForceBindIP installer verified. Extracting binaries...")
    seven_zip = ensure_7z(work_dir)
    extracted_dir = work_dir / "extracted"
    subprocess.run([str(seven_zip), "x", str(installer_file), f"-o{extracted_dir}", "-y"], check=True, capture_output=True)

    for filename in REQUIRED_FILES:
        src = extracted_dir / filename
        if not src.is_file():
            raise FileNotFoundError(f"Missing {filename} in extracted ForceBindIP")
        shutil.copy2(src, output_dir / filename)

    print(f"ForceBindIP successfully placed in {output_dir}:")
    for f in REQUIRED_FILES:
        print(f"  - {f} ({(output_dir / f).stat().st_size} bytes)")
    return output_dir


if __name__ == "__main__":
    fetch_forcebindip()
