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
    parser.add_argument("--list-profiles", action="store_true", help="Print all configured profiles and rules and exit")
    parser.add_argument("--list-adapters", action="store_true", help="Print detected network adapters and exit")
    parser.add_argument("--activate-profile", type=str, metavar="NAME", help="Activate profile by name on launch")
    parser.add_argument("--launch-rule", type=str, metavar="NAME", help="Launch a configured application rule by name")
    args = parser.parse_args()
    root = data_dir()
    root.mkdir(parents=True, exist_ok=True)
    store = ProfileManager(root)
    profiles = store.load_all()
    if not profiles and not store.errors:
        profiles = [Profile("Default", "Your everyday application routes")]
        store.save(profiles[0])

    if args.list_profiles:
        for p in profiles:
            trig = f" [Wi-Fi: {p.wifi_ssid}]" if p.wifi_ssid else (" [Startup]" if p.startup else "")
            print(f"Profile: {p.name}{trig}")
            for r in p.rules:
                status = "enabled" if r.enabled else "disabled"
                net = r.adapter.name if r.adapter else "Automatic"
                print(f"  - {r.name} [{status}] -> {net} ({r.executable})")
        return 0

    if args.list_adapters:
        from services.windows_network import discover_adapters, get_connected_wifi_ssid
        try:
            adapters = discover_adapters()
            ssid = get_connected_wifi_ssid()
            if ssid:
                print(f"Active Wi-Fi SSID: {ssid}")
            for a in adapters:
                reach = "Internet Reachable" if getattr(a, "has_internet", False) else "Local Only"
                print(f"[{a.status}] {a.identity.name} ({a.identity.description})")
                print(f"   IPv4: {', '.join(a.ipv4) or 'None'} | Status: {reach} | Type: {a.kind}")
        except Exception as err:
            print("Error discovering adapters:", err)
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName("NetDirector")
    app.setOrganizationName("NetDirector")
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    lock = QLockFile(str(root / "instance.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(None, "NetDirector", "NetDirector is already running. Open it from the system tray.")
        return 0
    settings = Settings(root)
    if args.activate_profile:
        matched = next((p for p in profiles if p.name.lower() == args.activate_profile.lower()), None)
        if matched:
            settings.values["last_profile"] = matched.id
            settings.values["restore_active"] = True
    logger = setup_logging(root, settings["diagnostic_logging"])
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
