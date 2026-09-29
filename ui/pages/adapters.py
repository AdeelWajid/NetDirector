from qt_compat.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QMessageBox
from ui.widgets import label, button, table, set_rows


class AdaptersPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.show_all = QCheckBox("Show disconnected and hidden interfaces")
        self.show_all.toggled.connect(self.refresh)
        row.addWidget(self.show_all)
        row.addStretch()
        row.addWidget(button("Adapter details", self.details))
        row.addWidget(button("Refresh networks", window.controller.refresh, True))
        layout.addLayout(row)
        self.table = table(["Adapter", "Description", "IPv4", "Status", "Type"],
                           stretch_column=1, column_widths={0: 200, 2: 160, 3: 100, 4: 110})
        self.table.doubleClicked.connect(lambda _: self.details())
        layout.addWidget(self.table)
        layout.addWidget(label("Read-only discovery. NetDirector does not modify routes, metrics, gateways, DNS, or firewall rules.", "muted"))
        self.visible_adapters = []

    def refresh(self):
        self.visible_adapters = [a for a in self.window.controller.adapters if self.show_all.isChecked() or a.available]
        ssid = getattr(self.window.controller, "current_ssid", "")
        def status_label(a):
            if a.available:
                return "Online (Internet)" if getattr(a, "has_internet", False) else "Connected (LAN)"
            return a.status
        def kind_label(a):
            if ssid and ("wi-fi" in a.identity.name.lower() or "wireless" in a.identity.description.lower()):
                return f"Wi-Fi • {ssid}"
            return a.kind

        set_rows(self.table, [(a.identity.name, a.identity.description, ", ".join(a.ipv4) or "—",
                               status_label(a), kind_label(a)) for a in self.visible_adapters])

    def details(self):
        index = self.table.currentRow()
        if not 0 <= index < len(self.visible_adapters):
            return
        a = self.visible_adapters[index]
        text = "\n".join([f"Description: {a.identity.description}",
                          f"Status: {a.status}",
                          f"Internet reachability: {'Reachable' if getattr(a, 'has_internet', False) else 'Local network only'}",
                          f"Type: {a.kind}",
                          f"IPv4: {', '.join(a.ipv4) or 'None'}", f"IPv6: {', '.join(a.ipv6) or 'None'}",
                          f"Gateways: {', '.join(a.gateways) or 'None'}", f"DNS: {', '.join(a.dns) or 'None'}",
                          f"MAC: {a.identity.mac}", f"GUID: {a.identity.guid}", f"Index: {a.identity.index}",
                          f"Link speed: {a.link_speed}"])
        QMessageBox.information(self, a.identity.name, text)
