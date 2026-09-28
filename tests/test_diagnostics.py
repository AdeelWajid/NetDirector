from types import SimpleNamespace
from core.process_manager import ProcessManager, Session
from models.application_rule import ApplicationRule
import core.process_manager as module


def test_diagnostics_classifies_actual_socket_addresses(monkeypatch):
    manager = ProcessManager()
    manager.sessions["r"] = Session("r", "app.exe", "App", "ForceBindIP", "192.0.2.19", 0, False,
                                    processes={123: 10}, ever_found=True)
    process = SimpleNamespace(create_time=lambda: 10, is_running=lambda: True, name=lambda: "app.exe",
                              net_connections=lambda **_: [SimpleNamespace(laddr=SimpleNamespace(ip=ip), status="ESTABLISHED")
                                                           for ip in ("192.0.2.19", "198.51.100.2", "0.0.0.0")])
    monkeypatch.setattr(module.psutil, "Process", lambda _: process)
    monkeypatch.setattr(module, "matching_processes", lambda _: [])
    result = manager.diagnostics(ApplicationRule("App", "app.exe", id="r"))
    assert [r["verdict"] for r in result] == ["Matches launch IP", "Different local IP", "Wildcard / loopback"]


def test_children_monitored_without_claiming_binding(monkeypatch):
    manager = ProcessManager()
    manager.sessions["r"] = Session("r", "app.exe", "App", "ForceBindIP", "192.0.2.19", 0, True,
                                    processes={123: 10}, ever_found=True)
    child = SimpleNamespace(pid=456, create_time=lambda: 11)
    root = SimpleNamespace(create_time=lambda: 10, is_running=lambda: True, children=lambda **_: [child])
    monkeypatch.setattr(module.psutil, "Process", lambda _: root)
    result = manager.update()["r"]
    assert set(result["pids"]) == {123, 456}
    assert result["status"] == "Running • binding unverified"
