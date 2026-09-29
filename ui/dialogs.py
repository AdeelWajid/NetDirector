from pathlib import Path
from qt_compat.QtCore import Qt, QFileInfo
from qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QCheckBox, QFileDialog, QDialogButtonBox, QMessageBox,
                             QFileIconProvider)
from models.application_rule import ApplicationRule
from ui.widgets import label, button, table, set_rows
from services.process_service import list_running_applications, discover_installed_games
from services.windows_network import get_connected_wifi_ssid

FALLBACK_LABELS = [("Do not launch application", "block"), ("Use Windows default route", "default"),
                   ("Ask me", "ask"), ("Wait until adapter reconnects", "wait")]


class ProcessPickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select running application")
        self.resize(780, 520)
        self.selected_app = None
        self.icons = QFileIconProvider()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addWidget(label("Running applications", "section"))
        layout.addWidget(label("Select any currently running application to automatically configure its rule.", "muted"))
        
        filter_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by application name, window title, or path…")
        self.search.textChanged.connect(self.filter_changed)
        filter_row.addWidget(self.search)
        self.hide_system = QCheckBox("Hide Windows system services")
        self.hide_system.setChecked(True)
        self.hide_system.toggled.connect(self.reload_data)
        filter_row.addWidget(self.hide_system)
        layout.addLayout(filter_row)
        
        self.table = table(["Application", "Window title", "PID", "Executable"],
                           stretch_column=[0, 1], column_widths={2: 85, 3: 250})
        self.table.doubleClicked.connect(lambda _: self.choose())
        layout.addWidget(self.table)
        
        btn_row = QHBoxLayout()
        btn_row.addWidget(button("Refresh processes", self.reload_data))
        btn_row.addStretch()
        btn_row.addWidget(button("Select application", self.choose, True))
        btn_row.addWidget(button("Cancel", self.reject))
        layout.addLayout(btn_row)
        
        self.all_apps = []
        self.displayed_apps = []
        self.reload_data()

    def reload_data(self):
        self.all_apps = list_running_applications(include_system=not self.hide_system.isChecked())
        self.filter_changed(self.search.text())

    def filter_changed(self, query):
        q = query.strip().lower()
        if not q:
            self.displayed_apps = self.all_apps
        else:
            self.displayed_apps = [a for a in self.all_apps
                                   if q in a["name"].lower() or q in a["title"].lower() or q in a["exe"].lower()]
        set_rows(self.table, [(a["name"], a["title"] or "—", str(a["pid"]), a["exe"]) for a in self.displayed_apps])
        for i, a in enumerate(self.displayed_apps):
            item = self.table.item(i, 0)
            if item:
                item.setIcon(self.icons.icon(QFileInfo(a["exe"])))

    def choose(self):
        idx = self.table.currentRow()
        if 0 <= idx < len(self.displayed_apps):
            self.selected_app = self.displayed_apps[idx]
            self.accept()
        else:
            QMessageBox.information(self, "Select application", "Please select an application from the table.")


class GamePickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Discover installed games")
        self.resize(780, 500)
        self.selected_game = None
        self.icons = QFileIconProvider()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addWidget(label("Installed games", "section"))
        layout.addWidget(label("Automatically discovered games from Steam, Epic Games, and system libraries.", "muted"))
        
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter games by title or executable path…")
        self.search.textChanged.connect(self.filter_changed)
        layout.addWidget(self.search)
        
        self.table = table(["Game title", "Platform", "Executable path"],
                           stretch_column=[0, 2], column_widths={1: 120})
        self.table.doubleClicked.connect(lambda _: self.choose())
        layout.addWidget(self.table)
        
        btn_row = QHBoxLayout()
        btn_row.addWidget(button("Scan again", self.reload_data))
        btn_row.addStretch()
        btn_row.addWidget(button("Add game rule", self.choose, True))
        btn_row.addWidget(button("Cancel", self.reject))
        layout.addLayout(btn_row)
        
        self.all_games = []
        self.displayed_games = []
        self.reload_data()

    def reload_data(self):
        self.all_games = discover_installed_games()
        self.filter_changed(self.search.text())

    def filter_changed(self, query):
        q = query.strip().lower()
        if not q:
            self.displayed_games = self.all_games
        else:
            self.displayed_games = [g for g in self.all_games
                                    if q in g["name"].lower() or q in g["executable"].lower()]
        set_rows(self.table, [(g["name"], g["launcher"], g["executable"]) for g in self.displayed_games])
        for i, g in enumerate(self.displayed_games):
            item = self.table.item(i, 0)
            if item:
                item.setIcon(self.icons.icon(QFileInfo(g["executable"])))

    def choose(self):
        idx = self.table.currentRow()
        if 0 <= idx < len(self.displayed_games):
            self.selected_game = self.displayed_games[idx]
            self.accept()
        else:
            QMessageBox.information(self, "Select game", "Please select a game from the list.")


class RuleDialog(QDialog):
    def __init__(self, adapters, settings, rule=None, executable="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit application" if rule else "Add application")
        self.resize(640, 660)
        self.rule = rule
        self.result_rule = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.addWidget(label(self.windowTitle(), "section"))
        layout.addWidget(label("Choose an application and the network to use at launch.", "muted"))
        form = QFormLayout()
        form.setVerticalSpacing(13)
        self.path = QLineEdit(rule.executable if rule else executable)
        browse_row = QHBoxLayout()
        browse_row.addWidget(self.path)
        browse_row.addWidget(button("Browse…", self.browse))
        browse_row.addWidget(button("Running apps…", self.pick_running))
        browse_row.addWidget(button("Scan games…", self.pick_game))
        form.addRow("Executable", browse_row)
        self.name = QLineEdit(rule.name if rule else Path(executable).stem)
        form.addRow("Display name", self.name)
        self.adapter = QComboBox()
        self.adapter.addItem("Automatic / Windows default", None)
        for adapter in adapters:
            self.adapter.addItem(f"{adapter.identity.name}  ·  {adapter.ip or adapter.status}  ·  #{adapter.identity.index}", adapter.identity)
        if rule and rule.adapter:
            index = next((i for i in range(1, self.adapter.count()) if self.adapter.itemData(i) == rule.adapter), -1)
            if index < 0:
                self.adapter.addItem(f"Saved: {rule.adapter.name} (resolve by identity)", rule.adapter)
                index = self.adapter.count() - 1
            self.adapter.setCurrentIndex(index)
        form.addRow("Preferred network", self.adapter)
        self.arguments = QLineEdit(rule.arguments if rule else "")
        self.arguments.setPlaceholderText('Example: --profile "Work"')
        form.addRow("Launch arguments", self.arguments)
        self.directory = QLineEdit(rule.working_directory if rule else "")
        self.directory.setPlaceholderText("Executable folder (default)")
        directory_row = QHBoxLayout()
        directory_row.addWidget(self.directory)
        directory_row.addWidget(button("Browse…", self.browse_directory))
        form.addRow("Working directory", directory_row)
        self.fallback = QComboBox()
        for text, value in FALLBACK_LABELS:
            self.fallback.addItem(text, value)
        self.fallback.setCurrentIndex(self.fallback.findData(rule.fallback if rule else settings["fallback"]))
        form.addRow("If unavailable", self.fallback)
        self.enabled = QCheckBox("Enable this rule")
        self.enabled.setChecked(rule.enabled if rule else True)
        self.auto = QCheckBox("Launch automatically when this profile activates")
        self.auto.setChecked(rule.auto_launch if rule else False)
        self.children = QCheckBox("Monitor child processes and their connections")
        self.children.setChecked(rule.children if rule else settings["children"] or Path(executable).stem.lower() == "steam")
        form.addRow(self.enabled)
        form.addRow(self.auto)
        form.addRow(self.children)
        layout.addLayout(form)
        layout.addWidget(label("Child binding: unavailable with ForceBindIP. Monitoring shows where observed child sockets connect; it does not force their route. Modern Chrome and some launchers are incompatible.", "muted"))
        layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def pick_running(self):
        dialog = ProcessPickerDialog(self)
        if dialog.exec() and dialog.selected_app:
            app = dialog.selected_app
            self.path.setText(app["exe"])
            current = self.name.text().strip()
            if not current or current == Path(app["exe"]).stem:
                self.name.setText(app["title"] if app["title"] else app["name"])
            if Path(app["exe"]).stem.lower() == "steam":
                self.children.setChecked(True)

    def pick_game(self):
        dialog = GamePickerDialog(self)
        if dialog.exec() and dialog.selected_game:
            game = dialog.selected_game
            self.path.setText(game["executable"])
            self.name.setText(game["name"])

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose application", "", "Windows applications (*.exe)")
        if path:
            self.path.setText(path)
            if not self.name.text().strip():
                self.name.setText(Path(path).stem)
            if Path(path).stem.lower() == "steam":
                self.children.setChecked(True)

    def browse_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Working directory")
        if path:
            self.directory.setText(path)

    def accept(self):
        path = Path(self.path.text().strip())
        if not self.name.text().strip() or path.suffix.lower() != ".exe" or not path.is_file():
            QMessageBox.warning(self, "Check application", "Enter a name and select an existing .exe file.")
            return
        if self.directory.text().strip() and not Path(self.directory.text().strip()).is_dir():
            QMessageBox.warning(self, "Check directory", "Choose an existing working directory.")
            return
        values = dict(name=self.name.text().strip(), executable=str(path.resolve()), adapter=self.adapter.currentData(),
                      arguments=self.arguments.text(), working_directory=self.directory.text().strip(),
                      enabled=self.enabled.isChecked(), auto_launch=self.auto.isChecked(),
                      children=self.children.isChecked(), fallback=self.fallback.currentData())
        if self.rule:
            values["id"] = self.rule.id
        self.result_rule = ApplicationRule(**values)
        super().accept()


class ProfileDialog(QDialog):
    def __init__(self, profile=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profile details")
        self.resize(520, 310)
        layout = QVBoxLayout(self)
        self.name = QLineEdit(profile.name if profile else "")
        self.description = QLineEdit(profile.description if profile else "")
        self.startup = QCheckBox("Load this profile on startup")
        self.startup.setChecked(profile.startup if profile else False)
        
        current_ssid = get_connected_wifi_ssid()
        self.wifi_ssid = QComboBox()
        self.wifi_ssid.setEditable(True)
        self.wifi_ssid.addItem("None (manual activation)", "")
        if current_ssid:
            self.wifi_ssid.addItem(f"Current Wi-Fi: {current_ssid}", current_ssid)
        if profile and profile.wifi_ssid and profile.wifi_ssid != current_ssid:
            self.wifi_ssid.addItem(f"Configured: {profile.wifi_ssid}", profile.wifi_ssid)
        if profile and profile.wifi_ssid:
            idx = self.wifi_ssid.findData(profile.wifi_ssid)
            if idx >= 0:
                self.wifi_ssid.setCurrentIndex(idx)
            else:
                self.wifi_ssid.setEditText(profile.wifi_ssid)
                
        form = QFormLayout()
        form.addRow("Name", self.name)
        form.addRow("Description", self.description)
        form.addRow("Wi-Fi SSID trigger", self.wifi_ssid)
        layout.addLayout(form)
        layout.addWidget(self.startup)
        layout.addWidget(label("Wi-Fi trigger automatically activates this profile when connecting to the specified SSID.", "muted"))
        layout.addWidget(label("Startup activation always waits for successful adapter discovery.", "muted"))
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Profile name", "Enter a profile name.")
            return
        super().accept()
