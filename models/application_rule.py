from dataclasses import dataclass, field
from uuid import uuid4
from models.adapter import AdapterIdentity

FALLBACKS = {"block", "default", "ask", "wait"}


@dataclass
class ApplicationRule:
    name: str
    executable: str
    adapter: AdapterIdentity | None = None
    arguments: str = ""
    working_directory: str = ""
    enabled: bool = True
    auto_launch: bool = False
    children: bool = False
    fallback: str = "block"
    id: str = field(default_factory=lambda: str(uuid4()))

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Application rule must be an object")
        values = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        if values.get("adapter") is not None:
            values["adapter"] = AdapterIdentity.from_dict(values["adapter"])
        rule = cls(**values)
        for key in ("name", "executable", "arguments", "working_directory", "id"):
            if not isinstance(getattr(rule, key), str):
                raise ValueError(f"Invalid rule {key}")
        if not rule.name.strip() or not rule.executable or not isinstance(rule.fallback, str) or rule.fallback not in FALLBACKS:
            raise ValueError("Invalid application name, executable, or fallback")
        for key in ("enabled", "auto_launch", "children"):
            if not isinstance(getattr(rule, key), bool):
                raise ValueError(f"Invalid rule {key}")
        return rule
