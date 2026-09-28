import struct
import pytest
from bindings.base_engine import BindingEngine, LaunchResult, argument_tokens
from bindings.forcebind_engine import ForceBindEngine
from core.adapter_manager import AdapterManager
from core.routing_service import RoutingService, AskFallback, WaitForAdapter
from models.adapter import Adapter, AdapterIdentity
from models.application_rule import ApplicationRule


class Recorder(BindingEngine):
    def launch_application(self, rule, current_ip):
        return current_ip


@pytest.fixture
def rule(tmp_path):
    path = tmp_path / "app.exe"
    path.write_bytes(b"MZ" + b"\0" * 58 + struct.pack("<I", 64) + b"PE\0\0" + struct.pack("<H", 0x8664))
    return ApplicationRule("App", str(path), AdapterIdentity(guid="wifi", name="Wi-Fi"))


def test_dhcp_refresh_immediately_before_launch(rule):
    addresses = iter(["192.0.2.5", "192.0.2.19"])
    manager = AdapterManager(lambda: [Adapter(rule.adapter, [next(addresses)], status="Up")])
    manager.refresh()
    service = RoutingService(manager, Recorder(), running=lambda _: [])
    assert service.launch(rule) == "192.0.2.19"


@pytest.mark.parametrize("fallback, exception", [("block", RuntimeError), ("ask", AskFallback), ("wait", WaitForAdapter)])
def test_missing_adapter(rule, fallback, exception):
    rule.fallback = fallback
    service = RoutingService(AdapterManager(lambda: []), Recorder(), running=lambda _: [])
    with pytest.raises(exception):
        service.launch(rule)


def test_fallback_default_and_explicit_ask(rule):
    service = RoutingService(AdapterManager(lambda: []), Recorder(), running=lambda _: [], default_launcher=lambda _: "default")
    rule.fallback = "default"
    assert service.launch(rule) == "default"
    rule.fallback = "ask"
    assert service.launch(rule, allow_default=True) == "default"


def test_missing_executable(rule):
    rule.executable += "missing"
    with pytest.raises(FileNotFoundError):
        RoutingService(AdapterManager(lambda: []), Recorder()).launch(rule)


def test_forcebind_command_arch_and_quoting(rule, tmp_path):
    (tmp_path / "ForceBindIP64.exe").touch()
    (tmp_path / "BindIP64.dll").touch()
    rule.arguments = '--title "two words" --flag'
    command = ForceBindEngine(str(tmp_path)).build_command(rule, "192.0.2.19")
    assert command[1:] == ["192.0.2.19", rule.executable, "--title", "two words", "--flag"]


def test_already_running(rule):
    with pytest.raises(RuntimeError, match="already running"):
        RoutingService(AdapterManager(lambda: []), Recorder(), running=lambda _: [123]).launch(rule)


def test_failed_scan_never_launches_even_with_default_fallback(rule):
    rule.fallback = "default"
    def fail():
        raise RuntimeError("scan failed")
    service = RoutingService(AdapterManager(fail), Recorder(), default_launcher=lambda _: pytest.fail("launched"))
    with pytest.raises(RuntimeError, match="scan failed"):
        service.launch(rule)
