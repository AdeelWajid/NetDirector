from pathlib import Path
from qt_compat.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QCheckBox, QFileDialog, QDialogButtonBox, QMessageBox)
from models.application_rule import ApplicationRule
from ui.widgets import label, button

FALLBACK_LABELS = [("Do not launch application", "block"), ("Use Windows default route", "default"),
                   ("Ask me", "ask"), ("Wait until adapter reconnects", "wait")]


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
        self.resize(480, 250)
        layout = QVBoxLayout(self)
        self.name = QLineEdit(profile.name if profile else "")
        self.description = QLineEdit(profile.description if profile else "")
        self.startup = QCheckBox("Load this profile on startup")
        self.startup.setChecked(profile.startup if profile else False)
        form = QFormLayout()
        form.addRow("Name", self.name)
        form.addRow("Description", self.description)
        layout.addLayout(form)
        layout.addWidget(self.startup)
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
