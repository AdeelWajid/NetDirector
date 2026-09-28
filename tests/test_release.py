import importlib.util
from pathlib import Path
import struct
import sys
import pytest
from qt_compat import BINDING

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from build_metadata import read_version, validate
from package_release import pe_architecture


def test_tag_must_match_version():
    version = read_version()
    assert validate("v" + version)[0] == version
    with pytest.raises(ValueError, match="must match"):
        validate("v999.999.999")


def test_wrong_interpreter_rejected():
    other = "x86" if struct.calcsize("P") == 8 else "x64"
    with pytest.raises(ValueError, match="interpreter"):
        validate(architecture=other)


@pytest.mark.parametrize("machine, expected", [(0x14C, "x86"), (0x8664, "x64"), (0xAA64, "unsupported")])
def test_release_pe_architecture(tmp_path, machine, expected):
    executable = tmp_path / "test.exe"
    executable.write_bytes(b"MZ" + b"\0" * 58 + struct.pack("<I", 64) + b"PE\0\0" + struct.pack("<H", machine))
    assert pe_architecture(executable) == expected


def test_runtime_matches_process_bitness():
    assert BINDING == ("PySide2" if struct.calcsize("P") == 4 else "PySide6")
