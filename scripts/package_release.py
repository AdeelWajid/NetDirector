"""Verify PE architecture, gather notices, zip the folder build, and checksum it."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile

from build_metadata import ROOT, validate


def pe_architecture(path):
    with Path(path).open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("Package executable has no PE header")
        stream.seek(0x3C)
        offset = struct.unpack("<I", stream.read(4))[0]
        stream.seek(offset)
        if stream.read(4) != b"PE\0\0":
            raise ValueError("Invalid PE signature")
        machine = struct.unpack("<H", stream.read(2))[0]
    return {0x14C: "x86", 0x8664: "x64"}.get(machine, "unsupported")


def collect_notices(destination, architecture):
    licenses = destination / "licenses"
    licenses.mkdir(exist_ok=True)
    runtime = ["PySide2", "shiboken2"] if architecture == "x86" else ["PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6"]
    components = {}
    for name in runtime + ["psutil", "pyinstaller"]:
        distribution = metadata.distribution(name)
        components[name] = distribution.version
        count = 0
        for file in distribution.files or []:
            path = Path(str(file))
            if "licenses" not in [part.lower() for part in path.parts] and not any(word in path.name.lower() for word in ("license", "copying", "copyright", "notice")):
                continue
            source = Path(distribution.locate_file(file))
            if source.is_file() and source.suffix.lower() not in (".pyc", ".dll", ".pyd", ".exe"):
                target = licenses / name / path.name
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.read_bytes() != source.read_bytes():
                    target = target.with_name(f"{count}-{target.name}")
                shutil.copyfile(source, target)
                count += 1
        if not count:
            raise RuntimeError(f"No license files found for {name}; do not publish a package without its notices")
    python_license = next((Path(p) / filename for p in (sys.base_prefix, sys.prefix)
                           for filename in ("LICENSE.txt", "LICENSE") if (Path(p) / filename).is_file()), None)
    if python_license is None:
        raise RuntimeError("Python runtime license could not be found")
    shutil.copyfile(python_license, licenses / "Python-LICENSE.txt")
    return components


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--architecture", choices=["x86", "x64"], required=True)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    version, architecture = validate(args.tag, args.architecture)
    source = ROOT / "dist" / architecture / "NetDirector"
    if pe_architecture(source / "NetDirector.exe") != architecture:
        raise ValueError("Executable architecture does not match its release label")
    for filename in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copyfile(ROOT / filename, source / filename)
    shutil.copytree(ROOT / "docs" / "screenshots", source / "docs" / "screenshots", dirs_exist_ok=True)
    shutil.copyfile(ROOT / "docs" / "USER_GUIDE.md", source / "docs" / "USER_GUIDE.md")
    components = collect_notices(source, architecture)
    (source / "BUILD_INFO.json").write_text(json.dumps(dict(version=version, architecture=architecture,
        python=sys.version.split()[0], legacy=architecture == "x86", components=components), indent=2), encoding="utf-8")
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    archive = release / f"NetDirector-{version}-windows-{architecture}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                package.write(path, path.relative_to(source.parent))
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise RuntimeError("Release ZIP failed integrity verification")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"Verified {archive.name} ({architecture}); SHA256 {digest}")


if __name__ == "__main__":
    main()
