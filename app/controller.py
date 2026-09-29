"""Qt orchestration. All network/process work runs on one serial worker thread."""
import copy
import logging
from collections import deque
from qt_compat.QtCore import QObject, Signal, QRunnable, QThreadPool, QTimer
from bindings import create_engine
from core.adapter_manager import AdapterManager
from core.routing_service import RoutingService, AskFallback, WaitForAdapter, CancelledLaunch
from core.process_manager import ProcessManager
from core.traffic_monitor import TrafficMonitor
from app.startup import select_startup_profile


class WorkerSignals(QObject):
    finished = Signal(object, object)


class Worker(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.operation()
            self.signals.finished.emit(result, None)
        except Exception as error:
            self.signals.finished.emit(None, error)


class Controller(QObject):
    changed = Signal()
    notice = Signal(str)
    error = Signal(str)
    fallback_requested = Signal(object, str)
    diagnostic_ready = Signal(object)
    busy_changed = Signal(bool)
    discovery_finished = Signal()
    profile_activated = Signal(str)

    def __init__(self, settings, profiles, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.profiles = profiles
        self.adapters = []
        self.states = {}
        self.sessions = {}
        self.traffic = {}
        self.active_profile = None
        self.current_ssid = ""
        self.ready = False
        self.startup_done = False
        self.busy = False
        self.queue = deque()
        self.pending = {}
        self.launching = set()
        self.generation = 0
        self.manager = AdapterManager()
        self.routing = RoutingService(self.manager, create_engine(settings))
        self.processes = ProcessManager()
        self.monitor = TrafficMonitor()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.periodic_refresh)
        self.sample_timer = QTimer(self)
        self.sample_timer.setInterval(2500)
        self.sample_timer.timeout.connect(self.sample)
        self.configure_timers()
        self.sample_timer.start()

    def configure_timers(self):
        self.timer.setInterval(self.settings["refresh_seconds"] * 1000)
        self.timer.start() if self.settings["auto_refresh"] else self.timer.stop()

    def submit(self, operation, callback, busy=True):
        self.queue.append((operation, callback, busy))
        self.next_job()

    def next_job(self):
        if self.busy or not self.queue:
            return
        operation, callback, busy = self.queue.popleft()
        if busy:
            self.busy = True
            self.busy_changed.emit(True)
        self.worker = Worker(operation)
        self.worker.signals.finished.connect(lambda result, error: self.job_finished(callback, result, error, busy))
        self.pool.start(self.worker)

    def job_finished(self, callback, result, error, busy):
        if busy:
            self.busy = False
        try:
            callback(result, error)
        except Exception as exc:
            logging.getLogger("netdirector").exception("Could not apply operation result")
            self.error.emit(str(exc))
        if busy:
            has_busy = any(b for _, _, b in self.queue)
            self.busy_changed.emit(self.busy or has_busy)
        self.next_job()

    def log(self, message):
        logging.getLogger("netdirector").info(message)
        self.notice.emit(message)

    def refresh(self, silent=False):
        if self.busy:
            if not silent:
                self.notice.emit("An operation is in progress; adapters will refresh shortly.")
            return
        if not silent:
            self.log("Adapter discovery started")
        else:
            logging.getLogger("netdirector").info("Periodic adapter discovery started")
        self.submit(self.manager.refresh, self.refreshed)

    def periodic_refresh(self):
        if not self.busy and not self.queue:
            self.refresh(silent=True)

    def refreshed(self, adapters, error):
        if error:
            self.ready = False
            self.states = {}
            self.error.emit(str(error))
            self.changed.emit()
            return
        old = {a.identity.guid: a.ip for a in self.adapters}
        self.adapters = adapters
        self.ready = True
        logging.getLogger("netdirector").info("Adapter discovery complete: %d interfaces, %d available", len(adapters), sum(a.available for a in adapters))
        for adapter in adapters:
            if adapter.identity.guid in old and old[adapter.identity.guid] != adapter.ip:
                self.log(f"{adapter.identity.name}: address changed. New launches use the current address; existing processes require restart.")
        self.update_states()
        if not self.startup_done:
            self.startup_done = True
            profile = select_startup_profile(self.profiles, self.settings, True)
            if profile:
                self.activate(profile)
            self.discovery_finished.emit()
        try:
            from services.windows_network import get_connected_wifi_ssid
            ssid = get_connected_wifi_ssid()
            self.current_ssid = ssid
            if ssid:
                matched = next((p for p in self.profiles if p.wifi_ssid and p.wifi_ssid.strip().lower() == ssid.lower()), None)
                if matched and self.active_profile != matched.id:
                    self.log(f"Connected to Wi-Fi '{ssid}': auto-activating profile '{matched.name}'")
                    self.activate(matched)
                    self.notice.emit(f"Switched to '{matched.name}' profile (connected to Wi-Fi: {ssid})")
        except Exception:
            pass
        for key, (rule, generation) in list(self.pending.items()):
            if generation != self.generation:
                self.pending.pop(key, None)
            elif self.routing.validate(rule).ip:
                self.pending.pop(key, None)
                self.launch(rule)
        self.changed.emit()

    def update_states(self):
        self.states = {r.id: self.routing.validate(r) for p in self.profiles for r in p.rules}

    def activate(self, profile):
        if not self.ready:
            self.error.emit("Wait for successful adapter discovery before activating a profile.")
            return
        self.generation += 1
        self.pending.clear()
        self.active_profile = profile.id
        self.profile_activated.emit(profile.id)
        self.settings.values["last_profile"] = profile.id
        self.settings.save()
        self.log(f"{profile.name} activated. Enabled automatic-launch rules are queued.")
        self.update_states()
        for rule in profile.rules:
            if rule.enabled and rule.auto_launch:
                self.launch(rule)
        self.changed.emit()

    def deactivate(self):
        self.generation += 1
        self.pending.clear()
        self.active_profile = None
        self.settings.values["last_profile"] = ""
        self.settings.save()
        self.log("Profile paused. Queued launches cancelled; running applications keep their launch-time binding until closed.")
        self.changed.emit()

    def launch(self, rule, allow_default=False):
        if rule.id in self.launching:
            return
        snapshot = copy.deepcopy(rule)
        generation = self.generation
        self.launching.add(rule.id)
        def operation():
            if generation != self.generation:
                return None
            self.routing.engine = create_engine(self.settings)
            result = self.routing.launch(snapshot, allow_default, cancelled=lambda: generation != self.generation)
            self.processes.register(snapshot, result)
            return result
        def completed(result, error):
            self.launching.discard(rule.id)
            self.adapters = self.manager.adapters
            self.ready = self.manager.ready
            self.update_states()
            if isinstance(error, CancelledLaunch):
                self.log(str(error))
            elif isinstance(error, AskFallback):
                if generation == self.generation:
                    self.fallback_requested.emit(snapshot, str(error))
            elif isinstance(error, WaitForAdapter):
                if generation == self.generation:
                    self.pending[rule.id] = (snapshot, generation)
                    self.log(f"{rule.name}: waiting for adapter")
            elif error:
                self.error.emit(str(error))
            elif result:
                self.log(f"{rule.name}: {result.status}")
                if rule.children and result.expected_ip:
                    self.log("Child processes are monitored only. ForceBindIP does not guarantee inherited binding.")
            self.changed.emit()
        self.submit(operation, completed)

    def sample(self):
        if self.busy or self.queue:
            return
        def operation():
            return self.monitor.sample(), self.processes.update()
        def completed(result, error):
            if not error:
                self.traffic, self.sessions = result
                self.changed.emit()
        self.submit(operation, completed, busy=False)

    def diagnose(self, rule):
        snapshot = copy.deepcopy(rule)
        def completed(result, error):
            self.error.emit(str(error)) if error else self.diagnostic_ready.emit(result)
        self.submit(lambda: self.processes.diagnostics(snapshot), completed)
