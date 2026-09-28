from app.startup import select_startup_profile
from models.profile import Profile
from utils.config import DEFAULTS
import pytest


def test_startup_discovery_barrier():
    profile = Profile("Gaming", startup=True)
    assert select_startup_profile([profile], DEFAULTS, False) is None
    assert select_startup_profile([profile], DEFAULTS, True) is profile


def test_conflicting_startup_profiles_block():
    with pytest.raises(ValueError, match="Multiple"):
        select_startup_profile([Profile("a", startup=True), Profile("b", startup=True)], DEFAULTS, True)


def test_startup_disabled_and_restore():
    profile = Profile("Gaming", startup=True)
    settings = dict(DEFAULTS, load_startup=False)
    assert select_startup_profile([profile], settings, True) is None
    settings.update(restore_active=True, last_profile=profile.id)
    assert select_startup_profile([profile], settings, True) is profile
