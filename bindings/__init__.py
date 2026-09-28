from bindings.forcebind_engine import ForceBindEngine
from bindings.bindip_engine import BindIPEngine
from bindings.native_engine import NativeEngine


def create_engine(settings):
    return {"ForceBindIP": lambda: ForceBindEngine(settings["forcebind_path"]),
            "BindIP": lambda: BindIPEngine(settings["bindip_path"]),
            "Native": NativeEngine}[settings["backend"]]()
