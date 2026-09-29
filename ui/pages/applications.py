from qt_compat.QtCore import Qt, QFileInfo
from qt_compat.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileIconProvider, QMenu
from ui.widgets import label, button, table, set_rows
from ui.design import panel, line_icon


class ApplicationsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.icons = QFileIconProvider()
        self.icon_cache = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(label("Applications in this profile", "section"))
        row.addStretch()
        row.addWidget(button("Scan games…", self.discover_games))
        row.addWidget(button("Add Steam", window.add_steam))
        row.addWidget(button("Add application", window.add_rule, True))
        layout.addLayout(row)
        self.empty = panel()
        empty_layout = QVBoxLayout(self.empty)
        empty_layout.setContentsMargins(40, 40, 40, 40)
        empty_layout.setSpacing(18)
        empty_layout.addStretch()
        symbol = label("")
        symbol.setPixmap(line_icon("route", "#bd9cdb", 84).pixmap(84, 84))
        empty_layout.addWidget(symbol, 0, Qt.AlignCenter)
        empty_layout.addWidget(label("A connection for every application", "section"), 0, Qt.AlignCenter)
        empty_description = label("Choose an app, then choose its network.\nOr drag an .exe onto this page.", "muted")
        empty_description.setWordWrap(False)
        empty_description.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_description, 0, Qt.AlignCenter)
        empty_layout.addWidget(button("Create your first rule", window.add_rule, True), 0, Qt.AlignCenter)
        empty_layout.addStretch()
        layout.addWidget(self.empty, 1)
        self.table = table(["Application", "Preferred network", "Current IP", "Status"],
                           stretch_column=[0, 1], column_widths={2: 160, 3: 170})
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        self.table.doubleClicked.connect(lambda _: window.edit_rule())
        layout.addWidget(self.table)
        row = QHBoxLayout()
        self.rule_buttons = [button("Launch selected", window.launch_selected, True),
                             button("Edit / change network", window.edit_rule),
                             button("Enable / disable", window.toggle_rule),
                             button("Remove", window.remove_rule)]
        for action in self.rule_buttons:
            row.addWidget(action)
        row.addStretch()
        layout.addLayout(row)
        layout.addWidget(label("Automatic uses Windows routing. Adapter rules resolve the current IP immediately before launch.", "muted"))
        self.setAcceptDrops(True)

    def selected(self):
        profile = self.window.current_profile()
        index = self.table.currentRow()
        return profile.rules[index] if profile and 0 <= index < len(profile.rules) else None

    def refresh(self):
        profile = self.window.current_profile()
        rules = profile.rules if profile else []
        self.empty.setVisible(not rules)
        self.table.setVisible(bool(rules))
        for action in self.rule_buttons:
            action.setEnabled(bool(rules))
        set_rows(self.table, [self.window.rule_row(r) for r in rules])
        for i, rule in enumerate(rules):
            if rule.executable not in self.icon_cache:
                self.icon_cache[rule.executable] = self.icons.icon(QFileInfo(rule.executable))
            self.table.item(i, 0).setIcon(self.icon_cache[rule.executable])
            self.table.item(i, 0).setToolTip(rule.executable)

    def context_menu(self, position):
        item = self.table.itemAt(position)
        if not item:
            return
        self.table.selectRow(item.row())
        menu = QMenu(self)
        for text, callback in [("Launch", self.window.launch_selected), ("Change network / edit", self.window.edit_rule),
                               ("Enable / disable", self.window.toggle_rule), ("Remove", self.window.remove_rule)]:
            menu.addAction(text, callback)
        menu.exec(self.table.viewport().mapToGlobal(position))

    def dragEnterEvent(self, event):
        if any(u.isLocalFile() and u.toLocalFile().lower().endswith(".exe") for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".exe"):
                self.window.add_rule(executable=url.toLocalFile())
        event.acceptProposedAction()

    def discover_games(self):
        from ui.dialogs import GamePickerDialog
        dialog = GamePickerDialog(self)
        if dialog.exec() and dialog.selected_game:
            self.window.add_rule(executable=dialog.selected_game["executable"])
