"""Generate Windows version resources and validate version tags before building."""
import argparse
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]


def read_version():
    value = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", value) or any(int(n) > 65535 for n in value.split(".")):
        raise ValueError("VERSION must contain a three-part numeric version with components <= 65535")
    return value


def validate(tag="", architecture=""):
    version = read_version()
    actual = "x64" if struct.calcsize("P") == 8 else "x86"
    if architecture and actual != architecture:
        raise ValueError(f"Build requested {architecture} but this Python interpreter is {actual}")
    if tag and tag != "v" + version:
        raise ValueError(f"Release tag {tag!r} must match v{version} from VERSION")
    if actual == "x86" and sys.version_info[:2] != (3, 10):
        raise ValueError("Legacy x86 builds require Python 3.10")
    return version, actual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="")
    parser.add_argument("--architecture", choices=["x86", "x64"], default="")
    args = parser.parse_args()
    version, architecture = validate(args.tag, args.architecture)
    numbers = tuple(int(n) for n in version.split(".")) + (0,)
    resource = f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}, mask=0x3f,
                   flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'NetDirector contributors'),
    StringStruct('FileDescription', 'NetDirector - Application Network Routing'),
    StringStruct('FileVersion', '{version}'),
    StringStruct('InternalName', 'NetDirector'),
    StringStruct('OriginalFilename', 'NetDirector.exe'),
    StringStruct('ProductName', 'NetDirector'),
    StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
'''
    directory = ROOT / "build"
    directory.mkdir(exist_ok=True)
    (directory / "version_info.txt").write_text(resource, encoding="utf-8")
    print(f"NetDirector {version} • {architecture}")


if __name__ == "__main__":
    main()
