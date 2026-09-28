# Third-party components

The MIT license in this repository covers NetDirector's own code. Dependencies
retain their original licenses; they are not relicensed under MIT.

| Component | Used by | Project / license information |
|---|---|---|
| Python | Both packages | [Python license](https://docs.python.org/3/license.html) |
| PySide6, Shiboken6 and Qt 6 | x64 | [Qt for Python licensing](https://doc.qt.io/qtforpython-6/licenses.html) |
| PySide2, Shiboken2 and Qt 5 | Legacy x86 | [PySide2 package](https://pypi.org/project/PySide2/) |
| psutil | Both packages | [psutil / BSD-3-Clause](https://github.com/giampaolo/psutil/blob/master/LICENSE) |
| PyInstaller bootloader | Both packages | [PyInstaller license and distribution exception](https://pyinstaller.org/en/stable/license.html) |

PySide/Qt are distributed as separate dynamic libraries in the folder package.
Their applicable LGPL/GPL/commercial terms and module-specific licenses remain
in effect. The packaging script includes the installed distributions' license
files and Python's license in `licenses/`; consult those files before redistribution.
Qt source is available from [Qt's source archive](https://download.qt.io/official_releases/qt/)
and PySide/Shiboken source from [Qt for Python](https://code.qt.io/cgit/pyside/pyside-setup.git/).
For an offline redistribution, provide the corresponding source and notices as
required by the licenses applicable to your distribution.

ForceBindIP is an optional separately installed application. Its binaries are
**not included** in the repository or release ZIPs. Obtain it from its
[author](https://r1ch.net/projects/forcebindip) under the author's terms.
