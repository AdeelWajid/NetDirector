from bindings.base_engine import BindingEngine


class NativeEngine(BindingEngine):
    name = "Native"

    def launch_application(self, rule, current_ip):
        raise RuntimeError("The native Windows binding engine is not implemented. Select ForceBindIP.")
