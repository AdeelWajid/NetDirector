import json
from core.adapter_manager import AdapterManager, match_adapter
from models.adapter import Adapter, AdapterIdentity
from services.windows_network import parse_adapters


def test_discovery_parsing():
    rows = parse_adapters(json.dumps([dict(name="Wi-Fi", guid="a", index=4, status="Up",
                                          ipv4=["169.254.1.2", "192.0.2.19"], ipv6=["::1"], dns=["192.0.2.1"])]))
    assert rows[0].ip == "192.0.2.19" and rows[0].available


def test_renamed_adapter():
    saved = AdapterIdentity(guid="{a}", name="Old", index=2)
    current = Adapter(AdapterIdentity(guid="A", name="New", index=9))
    assert match_adapter(saved, [current]).adapter is current


def test_duplicate_names_and_recycled_index_do_not_match():
    saved = AdapterIdentity(guid="old", name="Wi-Fi", index=2)
    current = [Adapter(AdapterIdentity(guid=g, name="Wi-Fi", index=2)) for g in ("new", "other")]
    assert match_adapter(saved, current).adapter is None


def test_reinstall_mac_match():
    saved = AdapterIdentity(guid="old", mac="AA:BB", index=2)
    current = Adapter(AdapterIdentity(guid="new", mac="aa-bb", index=4))
    assert match_adapter(saved, [current]).adapter is current


def test_discovery_failure_invalidates_cache():
    manager = AdapterManager(lambda: [])
    manager.refresh()
    def fail():
        raise RuntimeError("Disconnected")
    manager.discover = fail
    try:
        manager.refresh()
    except RuntimeError:
        pass
    assert not manager.ready
