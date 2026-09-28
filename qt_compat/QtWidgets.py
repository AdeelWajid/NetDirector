from qt_compat import USE_QT5

if USE_QT5:
    from PySide2.QtWidgets import *  # noqa: F403

    for widget_class in (QApplication, QDialog, QMenu):
        if not hasattr(widget_class, "exec"):
            widget_class.exec = widget_class.exec_
else:
    from PySide6.QtWidgets import *  # noqa: F403
