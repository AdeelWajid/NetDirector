from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton
from ui.widgets import label, button
from ui.design import panel, line_icon, TrafficGauge, ActionTile


def mbps(value):
    return "—" if value is None else f"{value:.2f} Mbps"


class DashboardPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        overview = panel()
        layout = QVBoxLayout(overview)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(12)
        row = QHBoxLayout()
        row.addWidget(label("Welcome to your network.", "section"), 1)
        more = button("•••", lambda: window.nav.setCurrentRow(3))
        more.setToolTip("View all network adapters")
        more.setFixedSize(40, 30)
        row.addWidget(more)
        layout.addLayout(row)
        layout.addWidget(label("Every connection has a purpose. Give your apps a route\nand keep your favorite setup one touch away.", "muted"))
        layout.addStretch(1)
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.values = []
        for text, icon in [("Networks online", "wifi"), ("Application rules", "apps"), ("Apps running", "traffic")]:
            column = QVBoxLayout()
            symbol = label("")
            symbol.setPixmap(line_icon(icon, "#b7a4d0", 33).pixmap(33, 33))
            value = label("0", "metric")
            self.values.append(value)
            column.addWidget(symbol)
            column.addWidget(value)
            column.addWidget(label(text, "muted"))
            stats.addLayout(column, 1)
        layout.addLayout(stats)
        layout.addStretch(1)
        self.overview_footer = label("Waiting for adapter discovery", "online")
        layout.addWidget(self.overview_footer)
        grid.addWidget(overview, 0, 0)

        bandwidth = panel()
        layout = QVBoxLayout(bandwidth)
        layout.setContentsMargins(20, 23, 20, 17)
        gauges = QHBoxLayout()
        gauges.setSpacing(8)
        self.gauges = []
        for title, direction, color in [("Download", "download", "#7dc6ef"), ("Upload", "upload", "#ce77d5")]:
            column = QVBoxLayout()
            title_label = label(title, "section")
            title_label.setAlignment(Qt.AlignCenter)
            column.addWidget(title_label)
            gauge = TrafficGauge(direction, color)
            column.addWidget(gauge, 1)
            self.gauges.append(gauge)
            gauges.addLayout(column, 1)
        layout.addLayout(gauges, 1)
        self.traffic_caption = label("LIVE TRAFFIC  ·  Waiting for counter samples", "muted")
        self.traffic_caption.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.traffic_caption)
        grid.addWidget(bandwidth, 0, 1)

        tiles = QWidget()
        tile_grid = QGridLayout(tiles)
        tile_grid.setContentsMargins(0, 0, 0, 0)
        tile_grid.setSpacing(12)
        self.tiles = []
        actions = [
            ("Add application", "add", window.add_rule),
            ("Applications", "apps", lambda: window.nav.setCurrentRow(1)),
            ("Profiles", "profiles", lambda: window.nav.setCurrentRow(2)),
            ("Refresh", "refresh", window.controller.refresh),
            ("Networks", "network", lambda: window.nav.setCurrentRow(3)),
            ("Traffic", "traffic", lambda: window.nav.setCurrentRow(4)),
            ("Diagnostics", "shield", lambda: window.nav.setCurrentRow(5)),
            ("Settings", "settings", lambda: window.nav.setCurrentRow(6)),
        ]
        for i, (text, icon, callback) in enumerate(actions):
            tile = ActionTile(text, icon, callback, i == 0)
            tile_grid.addWidget(tile, i // 4, i % 4)
            self.tiles.append(tile)
        grid.addWidget(tiles, 1, 0)

        right = QWidget()
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        profile_card = panel()
        layout = QVBoxLayout(profile_card)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.addWidget(label("Your profile", "section"))
        profile_icon = label("")
        profile_icon.setPixmap(line_icon("route", "#cbb4e1", 56).pixmap(56, 56))
        profile_icon.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(profile_icon)
        self.profile_name = label("Default", "profileName")
        self.profile_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.profile_name)
        self.profile_detail = label("0 rules · Inactive", "muted")
        self.profile_detail.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.profile_detail)
        self.profile_toggle = QPushButton("Inactive  ○")
        self.profile_toggle.setObjectName("profileSwitch")
        self.profile_toggle.setCheckable(True)
        self.profile_toggle.setFixedHeight(36)
        self.profile_toggle.setMinimumWidth(124)
        self.profile_toggle.setAccessibleName("Activate or pause selected profile")
        self.profile_toggle.setToolTip("Activating launches rules with automatic launch enabled. Pausing does not stop running apps.")
        self.profile_toggle.clicked.connect(self.toggle_profile)
        layout.addWidget(self.profile_toggle, 0, Qt.AlignCenter)
        layout.addStretch()
        manage = button("Manage profiles  ›", lambda: window.nav.setCurrentRow(2))
        layout.addWidget(manage)
        right_layout.addWidget(profile_card, 1)

        network_card = panel()
        layout = QVBoxLayout(network_card)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.addWidget(label("Connections", "section"))
        symbol = label("")
        symbol.setPixmap(line_icon("shield", "#cbb4e1", 56).pixmap(56, 56))
        symbol.setAlignment(Qt.AlignCenter)
        layout.addWidget(symbol, 1)
        self.connection_labels = []
        for _ in range(2):
            name, address = label("", "online"), label("", "muted")
            layout.addWidget(name)
            layout.addWidget(address)
            self.connection_labels.append((name, address))
        self.extra_networks = label("", "muted")
        layout.addWidget(self.extra_networks)
        layout.addStretch()
        layout.addWidget(button("View adapters  ›", lambda: window.nav.setCurrentRow(3)))
        right_layout.addWidget(network_card, 1)
        grid.addWidget(right, 1, 1)

    def toggle_profile(self):
        profile = self.window.current_profile()
        if profile and self.window.controller.active_profile == profile.id:
            self.window.safe(self.window.controller.deactivate)
        else:
            self.window.activate_selected()
        self.refresh()

    def refresh(self):
        self.setUpdatesEnabled(False)
        try:
            controller = self.window.controller
            profile = self.window.current_profile()
            available = [a for a in controller.adapters if a.available] if controller.ready else []
            values = [len(available), len(profile.rules) if profile else 0,
                      sum(bool(s["pids"]) for s in controller.sessions.values())]
            for widget, value in zip(self.values, values):
                val_str = str(value)
                if widget.text() != val_str:
                    widget.setText(val_str)
            footer_text = "●  Adapters refreshed · Ready when you are" if controller.ready else "Waiting for successful adapter discovery"
            if self.overview_footer.text() != footer_text:
                self.overview_footer.setText(footer_text)
            counters = [controller.traffic.get(a.identity.name, {}) for a in available]
            for gauge, key in zip(self.gauges, ("down", "up")):
                measured = [c[key] for c in counters if c.get(key) is not None]
                gauge.set_value(sum(measured) if measured else None)
            sampled = sum(c.get("down") is not None for c in counters)
            caption = f"LIVE TRAFFIC  ·  {sampled} interfaces sampled" if sampled else "LIVE TRAFFIC  ·  Waiting for counter samples"
            if self.traffic_caption.text() != caption:
                self.traffic_caption.setText(caption)
            active = bool(profile and controller.active_profile == profile.id)
            prof_name = profile.name if profile else "No profile"
            if self.profile_name.text() != prof_name:
                self.profile_name.setText(prof_name)
                self.profile_name.setToolTip(prof_name)
            waiting = sum(r.id in controller.pending for r in profile.rules) if profile else 0
            detail = f"{len(profile.rules) if profile else 0} rules · {waiting} waiting" if waiting else f"{len(profile.rules) if profile else 0} rules · {'Active' if active else 'Inactive'}"
            if self.profile_detail.text() != detail:
                self.profile_detail.setText(detail)
            if self.profile_toggle.isChecked() != active:
                self.profile_toggle.setChecked(active)
            toggle_text = "Active  ●" if active else "Inactive  ○"
            if self.profile_toggle.text() != toggle_text:
                self.profile_toggle.setText(toggle_text)
            self.profile_toggle.setEnabled(controller.ready and profile is not None)
            for i, (name, address) in enumerate(self.connection_labels):
                adapter = available[i] if i < len(available) else None
                name_text = "●  " + adapter.identity.name if adapter else ("No connection" if i == 0 else "")
                addr_text = adapter.ip if adapter else ""
                if name.text() != name_text:
                    name.setText(name_text)
                if address.text() != addr_text:
                    address.setText(addr_text)
                is_vis = adapter is not None or i == 0
                if name.isVisible() != is_vis:
                    name.setVisible(is_vis)
                addr_vis = adapter is not None
                if address.isVisible() != addr_vis:
                    address.setVisible(addr_vis)
            extra = f"+ {len(available)-2} more available" if len(available) > 2 else "Current addresses · Auto-resolved"
            if self.extra_networks.text() != extra:
                self.extra_networks.setText(extra)
        finally:
            self.setUpdatesEnabled(True)
