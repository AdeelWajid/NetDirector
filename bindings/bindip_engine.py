from bindings.base_engine import BindingEngine


class BindIPEngine(BindingEngine):
    name = "BindIP"

    def __init__(self, path=""):
        self.path = path

    def launch_application(self, rule, current_ip):
        raise RuntimeError("BindIP integration is not available in this release. Select ForceBindIP. BindIP uses a different configuration model and is not command-compatible.")
