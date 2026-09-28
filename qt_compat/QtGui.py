from qt_compat import USE_QT5

if USE_QT5:
    from PySide2.QtGui import *  # noqa: F403
else:
    from PySide6.QtGui import *  # noqa: F403
