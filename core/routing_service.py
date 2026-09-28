from dataclasses import dataclass
from pathlib import Path
from bindings.base_engine import launch_default
from services.process_service import matching_processes


@dataclass
class RuleState:
    status: str
    ip: str = ""
    adapter_name: str = "Automatic"


class RoutingService:
    def __init__(self, adapters, engine, running=matching_processes, default_launcher=launch_default):
        self.adapters = adapters
        self.engine = engine
        self.running = running
        self.default_launcher = default_launcher

    def validate(self, rule):
        if not rule.enabled:
            return RuleState("Disabled")
        if not Path(rule.executable).is_file():
            return RuleState("Executable missing")
        if not self.adapters.ready:
            return RuleState("Waiting for adapter discovery")
        if rule.adapter is None:
            return RuleState("Ready • Windows default")
        match = self.adapters.resolve(rule.adapter)
        if match.adapter is None:
            return RuleState(match.reason, adapter_name=rule.adapter.name)
        adapter = match.adapter
        if not adapter.available:
            return RuleState("Waiting for adapter" if rule.fallback == "wait" else "Adapter unavailable",
                             adapter_name=adapter.identity.name)
        return RuleState("Ready", adapter.ip, adapter.identity.name)

    def launch(self, rule, allow_default=False, cancelled=lambda: False):
        # Mandatory discovery barrier on EVERY launch, including manual launches.
        self.adapters.refresh()
        state = self.validate(rule)
        if not rule.enabled:
            raise ValueError("This application rule is disabled")
        if not Path(rule.executable).is_file():
            raise FileNotFoundError("The executable has moved or been deleted. Edit this rule to select it again.")
        if rule.working_directory and not Path(rule.working_directory).is_dir():
            raise FileNotFoundError("The working directory does not exist")
        if self.running(rule.executable):
            raise RuntimeError("This application is already running. Close it completely before launching with a new network selection.")
        if cancelled():
            raise CancelledLaunch("Launch cancelled because the profile or rule changed")
        if rule.adapter is None:
            return self.default_launcher(rule)
        if state.ip:
            return self.engine.bind_application(rule, state.ip)
        if rule.fallback == "default" or (rule.fallback == "ask" and allow_default):
            return self.default_launcher(rule)
        if rule.fallback == "ask":
            raise AskFallback("The selected adapter is unavailable. Launch using Windows default for this launch?")
        if rule.fallback == "wait":
            raise WaitForAdapter("Waiting for adapter; the launch will retry after it reconnects")
        raise RuntimeError(state.status + ". Launch blocked by this rule's fallback setting.")


class AskFallback(RuntimeError):
    pass


class WaitForAdapter(RuntimeError):
    pass


class CancelledLaunch(RuntimeError):
    pass
