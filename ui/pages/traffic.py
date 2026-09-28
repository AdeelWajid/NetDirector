from qt_compat.QtWidgets import QWidget, QVBoxLayout
from ui.widgets import label, table, set_rows
from ui.pages.dashboard import mbps


def size(value):
    return f"{value / 1024**3:.2f} GiB"


class TrafficPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label("Live adapter activity", "section"))
        layout.addWidget(label("Measured from Windows byte counters every 2.5 seconds. Totals are cumulative OS counters.", "muted"))
        self.table = table(["Adapter", "Download", "Upload", "Received", "Sent"])
        layout.addWidget(self.table)
        layout.addWidget(label("Per-application bandwidth: unavailable. Socket diagnostics are provided separately; socket counts are not bandwidth measurements.", "muted"))

    def refresh(self):
        set_rows(self.table, [(name, mbps(data["down"]), mbps(data["up"]), size(data["received"]), size(data["sent"]))
                              for name, data in self.window.controller.traffic.items()])
