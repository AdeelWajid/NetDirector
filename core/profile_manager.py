import json
from pathlib import Path
from uuid import uuid4
from models.profile import Profile, now
from utils.config import atomic_json


class ProfileManager:
    def __init__(self, root):
        self.directory = Path(root) / "profiles"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.errors = []

    def load_all(self):
        profiles = []
        self.errors.clear()
        for file in sorted(self.directory.glob("*.json")):
            try:
                profile = self.read(file)
                if file.stem != profile.id or any(p.id == profile.id for p in profiles):
                    raise ValueError("Profile filename does not match its unique ID")
                profiles.append(profile)
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                self.errors.append(f"{file.name}: {exc}")
        return profiles

    @staticmethod
    def read(file):
        path = Path(file)
        if path.stat().st_size > 2_000_000:
            raise ValueError("Profile exceeds the 2 MB size limit")
        return Profile.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def save(self, profile):
        Profile.from_dict(profile.to_dict())
        profile.modified = now()
        atomic_json(self.directory / f"{profile.id}.json", profile.to_dict())

    def delete(self, profile):
        Profile.from_dict(profile.to_dict())
        (self.directory / f"{profile.id}.json").unlink(missing_ok=True)

    def duplicate(self, profile, name=None):
        result = Profile.from_dict(profile.to_dict())
        result.id = str(uuid4())
        result.name = name or f"{profile.name} (copy)"
        result.created = now()
        result.startup = False
        for rule in result.rules:
            rule.id = str(uuid4())
        self.save(result)
        return result

    def import_profile(self, path):
        profile = self.read(path)
        # Imported files never grant permission to launch programs automatically.
        profile.startup = False
        for rule in profile.rules:
            rule.auto_launch = False
        return self.duplicate(profile, profile.name)

    def export_profile(self, profile, path):
        atomic_json(Path(path), profile.to_dict())
