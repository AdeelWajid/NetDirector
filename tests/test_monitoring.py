from types import SimpleNamespace
from core.traffic_monitor import TrafficMonitor
from core.process_manager import ProcessManager, Session


def test_real_counter_deltas_and_reset():
    counters = iter([100, 350, 10])
    times = iter([1, 3, 5])
    monitor = TrafficMonitor(lambda **_: {"Wi-Fi": SimpleNamespace(bytes_recv=next(counters), bytes_sent=0)}, lambda: next(times))
    assert monitor.sample()["Wi-Fi"]["down"] is None
    assert monitor.sample()["Wi-Fi"]["down"] == 0.001
    assert monitor.sample()["Wi-Fi"]["down"] == 0


def test_recycled_pid_not_treated_as_original(monkeypatch):
    import core.process_manager as module
    manager = ProcessManager()
    manager.sessions["r"] = Session("r", "app.exe", "App", "ForceBindIP", "192.0.2.1", 0, True,
                                    processes={123: 10}, ever_found=True)
    monkeypatch.setattr(module.psutil, "Process", lambda _: SimpleNamespace(create_time=lambda: 20))
    assert manager.update()["r"]["pids"] == []
    assert manager.sessions["r"].status == "Exited"
