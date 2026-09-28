import argparse
import sys
from qt_compat.QtCore import QTimer, QLockFile
from qt_compat.QtWidgets import QApplication, QMessageBox
from app.controller import Controller
from core.profile_manager import ProfileManager
from models.profile import Profile
from ui.main_window import MainWindow
from ui.theme import apply_theme, watch_system_theme
from utils.paths import data_dir
from utils.config import Settings
from utils.logging import setup_logging


def run():
    parser = argparse.ArgumentParser(description="NetDirector")
    parser.add_argument("--startup", action="store_true")
    parser.add_argument("--smoke-test", action="store_true", help="Discover adapters and exit after 12 seconds without automatic launches")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("NetDirector")
    app.setOrganizationName("NetDirector")
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    root = data_dir()
    root.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(root / "instance.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(None, "NetDirector", "NetDirector is already running. Open it from the system tray.")
        return 0
    settings = Settings(root)
    logger = setup_logging(root, settings["diagnostic_logging"])
    store = ProfileManager(root)
    profiles = store.load_all()
    if not profiles and not store.errors:
        profiles = [Profile("Default", "Your everyday application routes")]
        store.save(profiles[0])
    if args.smoke_test:
        settings.values.update(welcomed=True, load_startup=False, restore_active=False, launch_minimized=False)
    apply_theme(app, settings["theme"], settings["compact"])
    watch_system_theme(app, lambda: apply_theme(app, settings["theme"], settings["compact"]))
    controller = Controller(settings, profiles)
    window = MainWindow(controller, store, settings, root)
    if not settings["launch_minimized"] or not window.tray.isVisible() or not settings["welcomed"]:
        window.show()
    else:
        window.hide()
    def errors():
        for message in ([settings.error] if settings.error else []) + store.errors:
            window.show_error(message)
    QTimer.singleShot(100, errors)
    QTimer.singleShot(150, controller.refresh)
    if args.smoke_test:
        QTimer.singleShot(12000, window.exit_app)
    def exception_hook(kind, value, traceback):
        logger.error("Unexpected application error", exc_info=(kind, value, traceback))
        window.show_error(f"Unexpected error: {value}")
    sys.excepthook = exception_hook
    result = app.exec()
    controller.pool.waitForDone(45000)
    lock.unlock()
    return result
