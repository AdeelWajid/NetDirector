import json
import pytest
from core.profile_manager import ProfileManager
from models.profile import Profile
from models.application_rule import ApplicationRule
from models.adapter import AdapterIdentity
from utils.config import Settings


def test_roundtrip_never_persists_ip(tmp_path):
    manager = ProfileManager(tmp_path)
    profile = Profile("Gaming", rules=[ApplicationRule("Steam", "C:/Steam/steam.exe", AdapterIdentity(guid="a", name="Wi-Fi"))])
    manager.save(profile)
    assert manager.load_all()[0] == profile
    raw = (manager.directory / f"{profile.id}.json").read_text()
    assert "ipv4" not in raw and "current_ip" not in raw


def test_import_disables_automatic_launch(tmp_path):
    manager = ProfileManager(tmp_path)
    source = Profile("Incoming", startup=True, rules=[ApplicationRule("App", "app.exe", auto_launch=True)])
    file = tmp_path / "incoming.json"
    manager.export_profile(source, file)
    imported = manager.import_profile(file)
    assert not imported.startup and not imported.rules[0].auto_launch
    assert imported.id != source.id


def test_corrupt_profile_retained(tmp_path):
    manager = ProfileManager(tmp_path)
    bad = manager.directory / "bad.json"
    bad.write_text("{")
    assert manager.load_all() == [] and manager.errors and bad.exists()


def test_duplicate_rules_rejected():
    p = Profile("x", rules=[ApplicationRule("A", "C:/A.exe"), ApplicationRule("B", "c:/a.exe")])
    with pytest.raises(ValueError, match="Duplicate"):
        Profile.from_dict(p.to_dict())


def test_profile_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError):
        ProfileManager(tmp_path).save(Profile("x", id="../outside"))


def test_settings_recovery(tmp_path):
    (tmp_path / "settings.json").write_text("broken")
    settings = Settings(tmp_path)
    assert settings.error
    settings.save()
    assert (tmp_path / "settings.invalid.json").read_text() == "broken"
    assert json.loads((tmp_path / "settings.json").read_text())["theme"] == "dark"
