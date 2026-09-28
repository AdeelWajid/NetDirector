from qt_compat.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QCheckBox, QComboBox, QSpinBox,
                              QLineEdit, QHBoxLayout, QFileDialog, QScrollArea)
from core.startup_manager import set_start_with_windows
from ui.dialogs import FALLBACK_LABELS
from ui.widgets import label, button
from ui.theme import apply_theme


class SettingsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.fields = {}
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 0, 24, 20)
        for heading, fields in [
            ("General", [("start_with_windows", "Start NetDirector with Windows"), ("launch_minimized", "Launch minimized"),
                         ("minimize_to_tray", "Minimize to tray when closed"), ("auto_refresh", "Automatically refresh adapters")]),
            ("Profiles", [("load_startup", "Load the selected startup profile"), ("restore_active", "Restore last active profile when no startup profile is selected")]),
            ("Binding & diagnostics", [("children", "Monitor child processes by default for new rules"),
                                       ("diagnostic_logging", "Enable diagnostic logging")])]:
            layout.addWidget(label(heading, "section"))
            for key, text in fields:
                field = QCheckBox(text)
                field.setChecked(window.settings[key])
                self.fields[key] = field
                layout.addWidget(field)
        layout.addWidget(label("Adapter discovery on startup is mandatory. Child-process binding is not supported by the current backend.", "muted"))
        form = QFormLayout()
        for key, title, options in [("theme", "Appearance", [("System", "system"), ("Light", "light"), ("Dark", "dark")]),
                                    ("backend", "Binding backend", [("ForceBindIP", "ForceBindIP"), ("BindIP (not implemented)", "BindIP"), ("Native (not implemented)", "Native")]),
                                    ("fallback", "Default fallback for new rules", FALLBACK_LABELS)]:
            field = QComboBox()
            for text, value in options:
                field.addItem(text, value)
            field.setCurrentIndex(field.findData(window.settings[key]))
            self.fields[key] = field
            form.addRow(title, field)
        compact = QCheckBox("Compact spacing")
        compact.setChecked(window.settings["compact"])
        self.fields["compact"] = compact
        form.addRow("Density", compact)
        interval = QSpinBox()
        interval.setRange(10, 300)
        interval.setSuffix(" seconds")
        interval.setValue(window.settings["refresh_seconds"])
        self.fields["refresh_seconds"] = interval
        form.addRow("Refresh frequency", interval)
        for key, title in [("forcebind_path", "ForceBindIP directory"), ("bindip_path", "BindIP path (reserved)")]:
            field = QLineEdit(window.settings[key])
            field.setPlaceholderText("Auto-detect" if key == "forcebind_path" else "Integration not available")
            self.fields[key] = field
            row = QHBoxLayout()
            row.addWidget(field)
            row.addWidget(button("Browse…", lambda checked=False, target=field: self.browse(target)))
            form.addRow(title, row)
        layout.addLayout(form)
        layout.addWidget(label("ForceBindIP requires the matching x86 / x64 loader and DLL. NetDirector detects the target executable's architecture. No administrator rights are required for ordinary use.", "muted"))
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        row = QHBoxLayout()
        row.addWidget(button("Open data folder", window.open_data_folder))
        row.addStretch()
        row.addWidget(button("Save settings", self.save, True))
        outer.addLayout(row)

    def browse(self, field):
        path = QFileDialog.getExistingDirectory(self, "Choose backend directory")
        if path:
            field.setText(path)

    def save(self):
        values = self.window.settings.values.copy()
        for key, widget in self.fields.items():
            if isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentData()
            elif isinstance(widget, QSpinBox):
                values[key] = widget.value()
            else:
                values[key] = widget.text().strip()
        try:
            if values["start_with_windows"] != self.window.settings["start_with_windows"]:
                set_start_with_windows(values["start_with_windows"])
            self.window.settings.values = values
            self.window.settings.save()
            self.window.controller.configure_timers()
            import logging
            logging.getLogger("netdirector").setLevel(logging.DEBUG if values["diagnostic_logging"] else logging.INFO)
            from qt_compat.QtWidgets import QApplication
            apply_theme(QApplication.instance(), values["theme"], values["compact"])
            self.window.notify("Settings saved")
        except (OSError, ValueError, RuntimeError) as error:
            self.window.show_error(str(error))
