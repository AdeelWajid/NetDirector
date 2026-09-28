from dataclasses import dataclass
from models.adapter import Adapter, AdapterIdentity
from services.windows_network import discover_adapters


def normal(value):
    return str(value).casefold().replace("{", "").replace("}", "").replace(":", "").replace("-", "").strip()


@dataclass
class Match:
    adapter: Adapter | None
    reason: str


def match_adapter(saved: AdapterIdentity, adapters: list[Adapter]) -> Match:
    # Index alone is never trustworthy: Windows reuses indexes after device removal.
    for field in ("guid", "mac"):
        value = normal(getattr(saved, field))
        candidates = [a for a in adapters if value and normal(getattr(a.identity, field)) == value]
        if len(candidates) == 1:
            return Match(candidates[0], f"Matched {field}")
        if len(candidates) > 1:
            return Match(None, "Adapter needs to be reassigned (ambiguous identity)")
    # A different present GUID or MAC is positive evidence of a different device.
    candidates = []
    for a in adapters:
        ident = a.identity
        if any(normal(getattr(saved, f)) and normal(getattr(ident, f))
               and normal(getattr(saved, f)) != normal(getattr(ident, f)) for f in ("guid", "mac")):
            continue
        description = bool(saved.description and normal(saved.description) == normal(ident.description))
        name = bool(saved.name and normal(saved.name) == normal(ident.name))
        index = bool(saved.index and saved.index == ident.index)
        if description and (name or index):
            candidates.append(a)
    if len(candidates) == 1:
        return Match(candidates[0], "Matched corroborated adapter identity")
    return Match(None, "Adapter needs to be reassigned" if candidates else "Adapter unavailable or needs to be reassigned")


class AdapterManager:
    def __init__(self, discover=discover_adapters):
        self.discover = discover
        self.adapters = []
        self.ready = False

    def refresh(self):
        self.ready = False
        self.adapters = self.discover()
        self.ready = True
        return self.adapters

    def resolve(self, identity):
        if not self.ready:
            return Match(None, "Waiting for adapter discovery")
        return match_adapter(identity, self.adapters)
