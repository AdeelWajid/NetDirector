from qt_compat.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from ui.widgets import label, button, table, set_rows


class ProfilesPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(label("A setup for every part of your day", "section"))
        row.addStretch()
        row.addWidget(button("Import…", window.import_profile))
        row.addWidget(button("Create profile", window.create_profile, True))
        layout.addLayout(row)
        self.table = table(["Profile", "Description", "Applications", "Startup", "State"])
        layout.addWidget(self.table)
        row = QHBoxLayout()
        for text, callback in [("Activate", self.activate), ("Edit / rename", window.edit_profile),
                               ("Duplicate", window.duplicate_profile), ("Export…", window.export_profile), ("Delete", window.delete_profile)]:
            row.addWidget(button(text, callback))
        row.addStretch()
        layout.addLayout(row)
        layout.addWidget(label("One startup profile at a time. Imported profiles have automatic launch disabled until you enable it.", "muted"))

    def selected(self):
        index = self.table.currentRow()
        return self.window.profiles[index] if 0 <= index < len(self.window.profiles) else self.window.current_profile()

    def activate(self):
        profile = self.selected()
        if profile:
            self.window.profile_combo.setCurrentIndex(self.window.profile_combo.findData(profile.id))
            self.window.activate_selected()

    def refresh(self):
        set_rows(self.table, [(p.name, p.description or "—", len(p.rules), "Enabled" if p.startup else "—",
                               "Active" if p.id == self.window.controller.active_profile else "Inactive") for p in self.window.profiles])
