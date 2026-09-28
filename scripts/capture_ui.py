"""Render real discovered adapters, without launching any application rules."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")
import tempfile
import argparse
from qt_compat.QtWidgets import QApplication
from qt_compat.QtTest import QTest
from app.controller import Controller
from core.profile_manager import ProfileManager
from models.profile import Profile
from models.adapter import Adapter, AdapterIdentity
from services.windows_network import discover_adapters
from ui.main_window import MainWindow
from ui.theme import apply_theme
from utils.config import Settings

parser = argparse.ArgumentParser()
parser.add_argument("--live", action="store_true", help="Capture real networks to the ignored local-screenshots folder")
args = parser.parse_args()
app = QApplication([])
app.setStyle("Fusion")
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    settings = Settings(root)
    settings.values["welcomed"] = True
    profiles = [Profile("Default", "Your everyday application routes")]
    controller = Controller(settings, profiles)
    controller.timer.stop()
    controller.sample_timer.stop()
    controller.adapters = discover_adapters() if args.live else [
        Adapter(AdapterIdentity(guid="documentation-wifi", name="Wi-Fi"), ["192.0.2.18"], status="Up"),
        Adapter(AdapterIdentity(guid="documentation-ethernet", name="Ethernet"), ["198.51.100.24"], status="Up"),
    ]
    controller.manager.adapters = controller.adapters
    controller.manager.ready = controller.ready = True
    if args.live:
        controller.monitor.sample()
        QTest.qWait(1000)
        controller.traffic = controller.monitor.sample()
    window = MainWindow(controller, ProfileManager(root), settings, root)
    window.statusBar().showMessage("Adapters refreshed • No profile active" if args.live else "Documentation preview • Example adapters • No live traffic samples")
    window.show()
    destination = Path(__file__).resolve().parents[1] / "docs" / ("local-screenshots" if args.live else "screenshots")
    destination.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        apply_theme(app, theme)
        window.refresh()
        app.processEvents()
        window.grab().save(str(destination / f"dashboard-{theme}.png"))
    for index, name in [(1, "applications"), (5, "diagnostics"), (6, "settings")]:
        window.nav.setCurrentRow(index)
        app.processEvents()
        window.grab().save(str(destination / f"{name}-dark.png"))
    window.exiting = True
    window.close()
