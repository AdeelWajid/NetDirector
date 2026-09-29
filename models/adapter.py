from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdapterIdentity:
    guid: str = ""
    index: int = 0
    mac: str = ""
    description: str = ""
    name: str = ""

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Adapter identity must be an object")
        identity = cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})
        if type(identity.index) is not int or identity.index < 0:
            raise ValueError("Adapter index must be a nonnegative integer")
        if any(not isinstance(getattr(identity, key), str) for key in ("guid", "mac", "description", "name")):
            raise ValueError("Adapter identifiers must be strings")
        if not any((identity.guid, identity.mac, identity.description, identity.name)):
            raise ValueError("Adapter identity is empty; select Automatic or a valid adapter")
        return identity


@dataclass
class Adapter:
    identity: AdapterIdentity
    ipv4: list[str] = field(default_factory=list)
    ipv6: list[str] = field(default_factory=list)
    gateways: list[str] = field(default_factory=list)
    dns: list[str] = field(default_factory=list)
    status: str = "Unknown"
    kind: str = "Network"
    link_speed: str = ""
    has_internet: bool = False

    @property
    def available(self):
        return self.status.lower() == "up" and bool(self.ipv4)

    @property
    def ip(self):
        return self.ipv4[0] if self.ipv4 else ""
