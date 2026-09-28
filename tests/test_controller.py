import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import time
from qt_compat.QtWidgets import QApplication
from qt_compat.QtCore import QThread
from qt_compat.QtTest import QTest
from app.controller import Controller
from models.profile import Profile
from models.application_rule import ApplicationRule
from models.adapter import Adapter, AdapterIdentity
from bindings.base_engine import LaunchResult
from utils.config import Settings


def pump_until(app, condition):
    until = time.monotonic() + 4
    while not condition() and time.monotonic() < until:
        app.processEvents()
        QTest.qWait(10)
    assert condition()


def test_startup_discovers_then_resolves_again_before_launch(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    executable = tmp_path / "app.exe"
    executable.touch()
    identity = AdapterIdentity(guid="wifi", name="Wi-Fi")
    rule = ApplicationRule("App", str(executable), identity, auto_launch=True)
    profile = Profile("Gaming", rules=[rule], startup=True)
    settings = Settings(tmp_path)
    controller = Controller(settings, [profile])
    controller.timer.stop()
    controller.sample_timer.stop()
    events = []
    def discover():
        assert QThread.currentThread() != app.thread()
        events.append("scan")
        return [Adapter(identity, ["192.0.2.5" if len(events) == 1 else "192.0.2.19"], status="Up")]
    class Engine:
        def bind_application(self, rule, ip):
            events.append(ip)
            return LaunchResult(999999, time.time(), "Test", ip, loader=True)
    controller.manager.discover = discover
    controller.routing.running = lambda _: []
    monkeypatch.setattr("app.controller.create_engine", lambda _: Engine())
    callbacks = []
    controller.changed.connect(lambda: callbacks.append(QThread.currentThread() == app.thread()))
    controller.refresh()
    pump_until(app, lambda: len(events) == 3 and not controller.busy)
    assert events == ["scan", "scan", "192.0.2.19"]
    assert controller.active_profile == profile.id
    assert all(callbacks)
    controller.pool.waitForDone()


def test_pause_during_discovery_cancels_launch(tmp_path):
    from core.adapter_manager import AdapterManager
    from core.routing_service import RoutingService, CancelledLaunch
    from bindings.native_engine import NativeEngine
    import pytest
    executable = tmp_path / "app.exe"
    executable.touch()
    rule = ApplicationRule("App", str(executable))
    service = RoutingService(AdapterManager(lambda: []), NativeEngine(), running=lambda _: [],
                             default_launcher=lambda _: pytest.fail("Launch should be cancelled"))
    with pytest.raises(CancelledLaunch):
        service.launch(rule, cancelled=lambda: True)
