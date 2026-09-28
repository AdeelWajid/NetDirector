from qt_compat.QtGui import QColor
from qt_compat.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPlainTextEdit, QTabWidget
from ui.widgets import label, button, table, set_rows


class DiagnosticsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.rule_combo = QComboBox()
        self.rule_combo.setMinimumWidth(220)
        self.rule_combo.currentIndexChanged.connect(self.update_summary)
        row.addWidget(self.rule_combo)
        row.addStretch()
        row.addWidget(button("Check network usage", self.check, True))
        layout.addLayout(row)
        self.summary = label("Select an application to inspect its processes and local addresses.", "muted")
        layout.addWidget(self.summary)
        self.tabs = QTabWidget()
        self.table = table(["Process", "PID", "Local address", "Socket status", "Observation"])
        self.tabs.addTab(self.table, "Connections & child processes")
        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMaximumBlockCount(1200)
        self.tabs.addTab(self.logs, "Activity log")
        layout.addWidget(self.tabs)
        layout.addWidget(label("Observations are a point-in-time sample, not proof of all traffic. Wildcard, DNS-service, IPv6, and short-lived connections may not confirm the selected route. Access-denied processes are marked unavailable.", "muted"))
        window.controller.diagnostic_ready.connect(self.show_results)
        self.ids = []

    def selected(self):
        profile = self.window.current_profile()
        return next((r for r in profile.rules if r.id == self.rule_combo.currentData()), None) if profile else None

    def refresh(self):
        profile = self.window.current_profile()
        rules = profile.rules if profile else []
        ids = [(r.id, r.name) for r in rules]
        if ids != self.ids:
            current = self.rule_combo.currentData()
            self.rule_combo.blockSignals(True)
            self.rule_combo.clear()
            for rule in rules:
                self.rule_combo.addItem(rule.name, rule.id)
            index = self.rule_combo.findData(current)
            self.rule_combo.setCurrentIndex(max(0, index))
            self.rule_combo.blockSignals(False)
            self.ids = ids
            self.table.setRowCount(0)
        self.update_summary()

    def update_summary(self):
        rule = self.selected()
        if not rule:
            self.summary.setText("Add an application to inspect its connections.")
            return
        session = self.window.controller.sessions.get(rule.id, {})
        state = self.window.controller.states.get(rule.id)
        self.summary.setText(f"{rule.executable}\nPreferred network: {rule.adapter.name if rule.adapter else 'Automatic'}   ·   Current IP: {state.ip if state and state.ip else '—'}\n"
                             f"Backend: {session.get('backend', self.window.settings['backend'])}   ·   PIDs: {', '.join(map(str, session.get('pids', []))) or 'Not observed'}   ·   Launch IP: {session.get('expected_ip') or '—'}")

    def check(self):
        rule = self.selected()
        if rule:
            self.window.controller.diagnose(rule)

    def show_results(self, rows):
        set_rows(self.table, [(r["process"], r["pid"], r["local"], r["status"], r["verdict"]) for r in rows])
        for i, row in enumerate(rows):
            if row["verdict"] == "Different local IP":
                for j in range(self.table.columnCount()):
                    self.table.item(i, j).setForeground(QColor("#d97706"))
        self.tabs.setCurrentIndex(0)
        if not rows:
            self.window.notify("No running process or observable sockets found for this application.")
