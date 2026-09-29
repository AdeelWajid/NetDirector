from pathlib import Path
from models.profile import Profile
from models.application_rule import ApplicationRule
from models.adapter import Adapter, AdapterIdentity
from core.profile_manager import ProfileManager
from services.process_service import list_running_applications, discover_installed_games
from services.windows_network import get_connected_wifi_ssid, check_adapter_internet


def test_profile_wifi_ssid_roundtrip(tmp_path):
    manager = ProfileManager(tmp_path)
    profile = Profile("Office Setup", wifi_ssid="Corporate-5G")
    manager.save(profile)
    loaded = manager.load_all()[0]
    assert loaded.wifi_ssid == "Corporate-5G"
    assert loaded.name == "Office Setup"


def test_running_applications_enumeration():
    apps = list_running_applications(include_system=True)
    assert isinstance(apps, list)
    assert len(apps) > 0
    first = apps[0]
    for key in ("pid", "name", "exe", "title", "is_system"):
        assert key in first
    assert Path(first["exe"]).is_file()


def test_game_discovery_returns_list():
    games = discover_installed_games()
    assert isinstance(games, list)
    for g in games:
        assert "name" in g
        assert "launcher" in g
        assert "executable" in g
        assert Path(g["executable"]).is_file()


def test_adapter_has_internet_field():
    ident = AdapterIdentity(guid="test-guid", name="Test Wi-Fi")
    adapter = Adapter(identity=ident, ipv4=["192.168.1.100"], status="Up", has_internet=True)
    assert adapter.has_internet is True
    assert adapter.available is True


def test_internet_check_invalid_ip():
    assert check_adapter_internet("") is False
    assert check_adapter_internet("240.0.0.1", timeout=0.1) is False
