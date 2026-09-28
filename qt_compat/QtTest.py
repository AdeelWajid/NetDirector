from qt_compat import USE_QT5

if USE_QT5:
    from PySide2.QtTest import *  # noqa: F403
    from PySide2.QtCore import QEventLoop, QTimer

    if not hasattr(QTest, "qWait"):
        def _qwait(milliseconds):
            loop = QEventLoop()
            QTimer.singleShot(milliseconds, loop.quit)
            loop.exec_()
        QTest.qWait = staticmethod(_qwait)
else:
    from PySide6.QtTest import *  # noqa: F403
