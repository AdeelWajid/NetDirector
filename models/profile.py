from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from uuid import uuid4, UUID
from models.application_rule import ApplicationRule
import ntpath


def now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Profile:
    name: str
    description: str = ""
    rules: list[ApplicationRule] = field(default_factory=list)
    startup: bool = False
    wifi_ssid: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    created: str = field(default_factory=now)
    modified: str = field(default_factory=now)
    schema_version: int = 1

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get("schema_version", 1) != 1:
            raise ValueError("Unsupported profile format")
        values = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        values["rules"] = [ApplicationRule.from_dict(r) for r in data.get("rules", [])]
        profile = cls(**values)
        UUID(profile.id)
        if not isinstance(profile.name, str) or not profile.name.strip():
            raise ValueError("Profile needs a name")
        if not isinstance(profile.description, str) or not isinstance(profile.startup, bool):
            raise ValueError("Invalid profile description or startup option")
        paths = [ntpath.normcase(ntpath.normpath(r.executable)) for r in profile.rules]
        if len(set(paths)) != len(paths) or len({r.id for r in profile.rules}) != len(profile.rules):
            raise ValueError("Duplicate application rules")
        return profile
