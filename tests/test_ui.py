import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from qt_compat.QtWidgets import QApplication
from app.controller import Controller
from core.profile_manager import ProfileManager
from models.profile import Profile
from models.adapter import Adapter, AdapterIdentity
from ui.main_window import MainWindow
from ui.theme import apply_theme
from utils.config import Settings


def test_all_pages_and_themes_render(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = Settings(tmp_path)
    settings.values["welcomed"] = True
    store = ProfileManager(tmp_path)
    profiles = [Profile("Default")]
    controller = Controller(settings, profiles)
    controller.timer.stop()
    controller.sample_timer.stop()
    window = MainWindow(controller, store, settings, tmp_path)
    controller.adapters = [Adapter(AdapterIdentity(guid="test", name="Test interface"), ["192.0.2.9"], status="Up")]
    controller.ready = True
    window.show()
    for theme in ("light", "dark"):
        apply_theme(app, theme)
        for page in range(8):
            window.nav.setCurrentRow(page)
            app.processEvents()
            assert not window.grab().isNull()
    window.exiting = True
    window.close()
