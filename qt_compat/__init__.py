"""Qt 6 on x64; Qt 5 legacy compatibility on 32-bit Windows.

Selection is based on the Python process architecture, not the OS architecture.
PySide6 does not distribute win32 wheels. No fallback masks a broken Qt install.
"""
import struct

USE_QT5 = struct.calcsize("P") == 4
BINDING = "PySide2" if USE_QT5 else "PySide6"
