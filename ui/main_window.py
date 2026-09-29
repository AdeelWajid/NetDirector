from pathlib import Path
from datetime import datetime
import copy
from qt_compat.QtCore import Qt, QTimer, QUrl
from qt_compat.QtGui import QIcon, QDesktopServices
from qt_compat.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QStackedWidget, QComboBox, QFrame,
                             QProgressBar, QMessageBox, QFileDialog, QSystemTrayIcon, QMenu, QStyle, QScrollArea)
from models.profile import Profile
from services.process_service import steam_path
from utils.paths import asset
from ui.widgets import label, button
from ui.design import NavigationBar, line_icon
from qt_compat import BINDING
from utils.version import VERSION
from ui.dialogs import RuleDialog, ProfileDialog
from ui.pages.dashboard import DashboardPage
from ui.pages.applications import ApplicationsPage
from ui.pages.profiles import ProfilesPage
from ui.pages.adapters import AdaptersPage
from ui.pages.traffic import TrafficPage
from ui.pages.diagnostics import DiagnosticsPage
from ui.pages.settings import SettingsPage

NAVIGATION = [
    ("Dashboard", "Your connections. Working together.", QStyle.SP_ComputerIcon),
    ("Applications", "Give every application a preferred network.", QStyle.SP_FileIcon),
    ("Profiles", "Switch between the setups that work for you.", QStyle.SP_DirIcon),
    ("Network Adapters", "A live view of your Windows interfaces.", QStyle.SP_DriveNetIcon),
    ("Traffic Monitor", "See how your connections are being used.", QStyle.SP_BrowserReload),
    ("Diagnostics", "Inspect processes, connections, and activity.", QStyle.SP_FileDialogDetailedView),
    ("Settings", "Make NetDirector work your way.", QStyle.SP_FileDialogContentsView),
    ("About", "Designed for deliberate network choices.", QStyle.SP_MessageBoxInformation),
]


class MainWindow(QMainWindow):
    def __init__(self, controller, store, settings, root):
        super().__init__()
        self.controller, self.store, self.settings, self.root = controller, store, settings, root
        self.profiles = controller.profiles
        self.exiting = False
        self.setWindowTitle("NetDirector")
        self.setWindowIcon(QIcon(str(asset("netdirector.ico"))))
        self.resize(1320, 860)
        self.setMinimumSize(1040, 700)
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(96)
        top = QHBoxLayout(topbar)
        top.setContentsMargins(30, 15, 30, 15)
        top.setSpacing(18)
        logo = label("")
        logo.setPixmap(line_icon("route", "#ffffff", 38).pixmap(38, 38))
        top.addWidget(logo)
        branding = QVBoxLayout()
        branding.setSpacing(3)
        self.brand = label("NetDirector", "brand")
        branding.addWidget(self.brand)
        tagline = label("YOUR NETWORK. YOUR RULES.", "brandSub")
        tagline.setWordWrap(False)
        branding.addWidget(tagline)
        top.addLayout(branding)
        top.addStretch(1)
        self.nav = NavigationBar()
        top.addWidget(self.nav)
        outer.addWidget(topbar)
        self.connection_badge = label("Discovering networks…", "pill")
        self.connection_badge.setWordWrap(False)
        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(30, 24, 30, 16)
        body.setSpacing(16)
        header = QHBoxLayout()
        headings = QVBoxLayout()
        self.title = label("Dashboard", "title")
        self.subtitle = label(NAVIGATION[0][1], "subtitle")
        headings.addWidget(self.title)
        headings.addWidget(self.subtitle)
        header.addLayout(headings, 1)
        header.addWidget(self.connection_badge, 0, Qt.AlignVCenter)
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.setToolTip("Selected profile — activation is a separate action")
        header.addWidget(self.profile_combo)
        body.addLayout(header)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedSize(140, 10)
        self.progress.hide()
        self.statusBar().addPermanentWidget(self.progress)
        self.banner = label("", "pill")
        self.banner.hide()
        body.addWidget(self.banner)
        self.banner_timer = QTimer(self)
        self.banner_timer.setSingleShot(True)
        self.banner_timer.timeout.connect(self.banner.hide)
        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(self)
        self.applications = ApplicationsPage(self)
        self.profile_page = ProfilesPage(self)
        self.adapter_page = AdaptersPage(self)
        self.traffic_page = TrafficPage(self)
        self.diagnostics = DiagnosticsPage(self)
        self.settings_page = SettingsPage(self)
        about = QWidget()
        about_outer = QVBoxLayout(about)
        about_outer.setContentsMargins(0, 0, 0, 0)
        about_scroll = QScrollArea()
        about_scroll.setWidgetResizable(True)
        about_content = QWidget()
        about_layout = QVBoxLayout(about_content)
        about_layout.setContentsMargins(6, 0, 24, 20)
        about_layout.setSpacing(14)
        about_layout.addWidget(label("NetDirector", "title"))
        about_layout.addWidget(label(f"Version {VERSION} • {BINDING} • {'x86 legacy' if BINDING == 'PySide2' else 'x64'}", "muted"))
        about_layout.addWidget(label("Developer & Project", "section"))
        about_layout.addWidget(label("NetDirector is created and maintained by Adeel Wajid.\nOpen-source Windows network routing and application binding director."))
        about_links = QHBoxLayout()
        about_links.setSpacing(10)
        about_links.addWidget(button("GitHub: @AdeelWajid", lambda: QDesktopServices.openUrl(QUrl("https://github.com/AdeelWajid")), primary=True))
        about_links.addWidget(button("Project Repository", lambda: QDesktopServices.openUrl(QUrl("https://github.com/AdeelWajid/NetDirector"))))
        about_links.addWidget(button("User Guide", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(asset("README.md"))))))
        about_links.addWidget(button("ForceBindIP Docs", lambda: QDesktopServices.openUrl(QUrl("https://r1ch.net/projects/forcebindip"))))
        about_links.addStretch()
        about_layout.addLayout(about_links)
        about_layout.addWidget(label("Profiles remember your adapters, not yesterday's IP addresses.", "section"))
        about_layout.addWidget(label("NetDirector discovers current interfaces before startup activation and again before every launch. It never changes global routing, adapter metrics, DNS, or firewall settings."))
        about_layout.addWidget(label("Backend capabilities", "section"))
        about_layout.addWidget(label("ForceBindIP: launch-time IPv4 binding for compatible x86 / x64 applications. Existing processes cannot be rebound. Child binding, modern Chrome support, IPv6 enforcement, and VPN leak prevention are not guaranteed. BindIP and native backends are extension points, not implemented engines."))
        about_layout.addStretch()
        about_scroll.setWidget(about_content)
        about_outer.addWidget(about_scroll)
        self.pages = [self.dashboard, self.applications, self.profile_page, self.adapter_page,
                      self.traffic_page, self.diagnostics, self.settings_page, about]
        for page in self.pages:
            self.stack.addWidget(page)
        body.addWidget(self.stack)
        outer.addWidget(content, 1)
        self.nav.currentRowChanged.connect(self.navigate)
        self.nav.setCurrentRow(0)
        self.profile_combo.currentIndexChanged.connect(self.refresh)
        self.reload_profiles()
        self.controller.changed.connect(self.refresh)
        self.controller.notice.connect(self.notify)
        self.controller.error.connect(self.show_error)
        self.controller.busy_changed.connect(self.progress.setVisible)
        self.controller.fallback_requested.connect(self.ask_fallback)
        self.controller.discovery_finished.connect(self.welcome)
        self.controller.profile_activated.connect(lambda identity: self.profile_combo.setCurrentIndex(self.profile_combo.findData(identity)))
        self.setup_tray()
        self.statusBar().showMessage("Discovering adapters before profile activation…")
        log_file = root / "logs" / "netdirector.log"
        if log_file.exists():
            self.diagnostics.logs.setPlainText(log_file.read_text(encoding="utf-8", errors="replace")[-70000:])

    def navigate(self, index):
        self.stack.setCurrentIndex(index)
        self.title.setText(NAVIGATION[index][0])
        self.subtitle.setText(NAVIGATION[index][1])
        self.refresh()

    def current_profile(self):
        return next((p for p in self.profiles if p.id == self.profile_combo.currentData()), None)

    def reload_profiles(self, selected=None):
        selected = selected or self.profile_combo.currentData()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in self.profiles:
            self.profile_combo.addItem(profile.name, profile.id)
        self.profile_combo.setCurrentIndex(max(0, self.profile_combo.findData(selected)))
        self.profile_combo.blockSignals(False)
        self.controller.update_states()
        self.refresh()

    def rule_row(self, rule):
        state = self.controller.states.get(rule.id)
        session = self.controller.sessions.get(rule.id)
        status = state.status if state else "Waiting for discovery"
        if rule.id in self.controller.pending:
            status = "Waiting for adapter"
        if rule.id in self.controller.launching:
            status = "Refreshing adapter / launching…"
        if session and session["pids"]:
            status = session["status"]
            if state and session["expected_ip"] and session["expected_ip"] != state.ip:
                status = "Address changed • restart required"
        return (rule.name, state.adapter_name if state else (rule.adapter.name if rule.adapter else "Automatic"),
                state.ip or "—" if state else "—", status)

    def refresh(self):
        if not hasattr(self, "pages"):
            return
        current = self.stack.currentWidget()
        if current and hasattr(current, "refresh"):
            current.refresh()
        self.connection_badge.setText(f"●  {sum(a.available for a in self.controller.adapters)} networks available" if self.controller.ready else "Discovery not ready")
        if hasattr(self, "tray_profile"):
            active = next((p.name for p in self.profiles if p.id == self.controller.active_profile), "None")
            self.tray_profile.setText("Current profile: " + active)
            self.rebuild_tray_profiles()

    def notify(self, message):
        self.statusBar().showMessage(message, 12000)
        self.banner.setText(message)
        self.banner.show()
        self.banner_timer.start(6500)
        self.diagnostics.logs.appendPlainText(datetime.now().strftime("%H:%M:%S") + "  " + message)

    def show_error(self, message):
        import logging
        logging.getLogger("netdirector").warning(message)
        self.notify("Attention: " + message)
        self.banner_timer.stop()
        if not self.isVisible() and self.tray.isVisible():
            self.tray.showMessage("NetDirector", message, QSystemTrayIcon.Warning)

    def safe(self, action):
        try:
            return action()
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            self.show_error(str(error))
            return None

    def activate_selected(self):
        profile = self.current_profile()
        if profile:
            self.safe(lambda: self.controller.activate(profile))

    def add_rule(self, checked=False, executable=""):
        profile = self.current_profile()
        if profile is None:
            self.create_profile()
            profile = self.current_profile()
        if profile is None:
            return
        dialog = RuleDialog(self.controller.adapters, self.settings, executable=executable, parent=self)
        if dialog.exec():
            updated = copy.deepcopy(profile)
            updated.rules.append(dialog.result_rule)
            self.commit_profile(updated)

    def edit_rule(self):
        rule = self.applications.selected()
        profile = self.current_profile()
        if not rule or not profile:
            self.notify("Select an application first.")
            return
        dialog = RuleDialog(self.controller.adapters, self.settings, rule=rule, parent=self)
        if dialog.exec():
            updated = copy.deepcopy(profile)
            updated.rules = [dialog.result_rule if r.id == rule.id else r for r in updated.rules]
            self.commit_profile(updated)

    def commit_profile(self, profile):
        def save():
            self.store.save(profile)
            for i, previous in enumerate(self.profiles):
                if previous.id == profile.id:
                    self.profiles[i] = profile
                    break
            else:
                self.profiles.append(profile)
            # Editing invalidates queued snapshots, preventing old rules from launching.
            self.controller.generation += 1
            self.controller.pending.clear()
            self.reload_profiles(profile.id)
            self.notify("Profile saved")
        self.safe(save)

    def toggle_rule(self):
        rule, profile = self.applications.selected(), self.current_profile()
        if rule and profile:
            updated = copy.deepcopy(profile)
            next(r for r in updated.rules if r.id == rule.id).enabled = not rule.enabled
            self.commit_profile(updated)

    def remove_rule(self):
        rule, profile = self.applications.selected(), self.current_profile()
        if rule and profile and QMessageBox.question(self, "Remove application", f"Remove {rule.name} from this profile?") == QMessageBox.Yes:
            updated = copy.deepcopy(profile)
            updated.rules = [r for r in updated.rules if r.id != rule.id]
            self.commit_profile(updated)

    def launch_selected(self):
        rule = self.applications.selected()
        if rule:
            self.controller.launch(rule)
        else:
            self.notify("Select an application first.")

    def add_steam(self):
        path = steam_path()
        if path:
            self.add_rule(executable=path)
        else:
            self.notify("Steam was not found in the usual locations. Browse for steam.exe.")
            self.add_rule()

    def ask_fallback(self, rule, message):
        self.open_window()
        if QMessageBox.question(self, f"{rule.name} • fallback", message) == QMessageBox.Yes:
            self.controller.launch(rule, allow_default=True)

    def create_profile(self):
        dialog = ProfileDialog(parent=self)
        if dialog.exec():
            ssid = dialog.wifi_ssid.currentData()
            if not ssid:
                ssid = dialog.wifi_ssid.currentText().strip()
                if "none" in ssid.lower():
                    ssid = ""
            profile = Profile(dialog.name.text().strip(), dialog.description.text().strip(),
                              startup=dialog.startup.isChecked(), wifi_ssid=ssid)
            self.save_profile_details(profile)

    def edit_profile(self):
        profile = self.profile_page.selected()
        if not profile:
            return
        dialog = ProfileDialog(profile, self)
        if dialog.exec():
            ssid = dialog.wifi_ssid.currentData()
            if not ssid:
                ssid = dialog.wifi_ssid.currentText().strip()
                if "none" in ssid.lower():
                    ssid = ""
            updated = copy.deepcopy(profile)
            updated.name, updated.description, updated.startup = dialog.name.text().strip(), dialog.description.text().strip(), dialog.startup.isChecked()
            updated.wifi_ssid = ssid
            self.save_profile_details(updated)

    def save_profile_details(self, profile):
        if profile.startup:
            for other in self.profiles:
                if other.id != profile.id and other.startup:
                    other.startup = False
                    if self.safe(lambda p=other: (self.store.save(p), True)[1]) is None:
                        return
        self.commit_profile(profile)

    def duplicate_profile(self):
        profile = self.profile_page.selected()
        if profile:
            duplicated = self.safe(lambda: self.store.duplicate(profile))
            if duplicated:
                self.profiles.append(duplicated)
                self.reload_profiles(duplicated.id)

    def delete_profile(self):
        profile = self.profile_page.selected()
        if profile and QMessageBox.question(self, "Delete profile", f"Delete {profile.name} and its saved rules?") == QMessageBox.Yes:
            def remove():
                self.store.delete(profile)
                self.controller.generation += 1
                self.controller.pending.clear()
                if self.controller.active_profile == profile.id:
                    self.controller.deactivate()
                self.profiles.remove(profile)
                self.reload_profiles()
            self.safe(remove)

    def export_profile(self):
        profile = self.profile_page.selected()
        if profile:
            path, _ = QFileDialog.getSaveFileName(self, "Export profile", "profile.json", "JSON profiles (*.json)")
            if path:
                self.safe(lambda: self.store.export_profile(profile, path))

    def import_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import profile", "", "JSON profiles (*.json)")
        if path:
            profile = self.safe(lambda: self.store.import_profile(path))
            if profile:
                self.profiles.append(profile)
                self.reload_profiles(profile.id)
                self.notify("Profile imported. Review executable paths before enabling automatic launch.")

    def open_data_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.root)))

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("NetDirector")
        menu = QMenu(self)
        menu.addAction("Open NetDirector", self.open_window)
        self.tray_profile = menu.addAction("Current profile: None")
        self.tray_profile.setEnabled(False)
        self.tray_profiles_menu = menu.addMenu("Switch profile")
        self.rebuild_tray_profiles()
        menu.addSeparator()
        menu.addAction("Activate selected profile", self.activate_selected)
        menu.addAction("Pause bindings / automatic launches", lambda: self.safe(self.controller.deactivate))
        menu.addAction("Refresh adapters", self.controller.refresh)
        menu.addAction("Settings", lambda: (self.open_window(), self.nav.setCurrentRow(6)))
        menu.addSeparator()
        menu.addAction("Exit", self.exit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.open_window() if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def rebuild_tray_profiles(self):
        if not hasattr(self, "tray_profiles_menu"):
            return
        self.tray_profiles_menu.clear()
        for p in self.profiles:
            action = self.tray_profiles_menu.addAction(p.name)
            action.setCheckable(True)
            action.setChecked(p.id == self.controller.active_profile)
            action.triggered.connect(lambda checked=False, pid=p.id: self.switch_profile_by_id(pid))

    def switch_profile_by_id(self, profile_id):
        idx = self.profile_combo.findData(profile_id)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
            self.activate_selected()

    def open_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if not self.exiting and self.settings["minimize_to_tray"] and self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            if self.controller.busy or self.controller.queue:
                self.notify("Finishing the current operation before exit…")
                event.ignore()
                self.exit_app()
                return
            self.tray.hide()
            event.accept()
            from qt_compat.QtWidgets import QApplication
            QApplication.instance().quit()

    def exit_app(self):
        self.exiting = True
        self.controller.generation += 1
        self.controller.pending.clear()
        self.controller.timer.stop()
        self.controller.sample_timer.stop()
        if self.controller.busy or self.controller.queue:
            QTimer.singleShot(200, self.exit_app)
        else:
            self.close()

    def welcome(self):
        if self.settings["welcomed"]:
            return
        networks = [a.identity.name for a in self.controller.adapters if a.available]
        box = QMessageBox(self)
        box.setWindowTitle("Welcome to NetDirector")
        box.setText("Control which network connection each Windows application uses.")
        box.setInformativeText("Detected networks\n" + ("\n".join("✓ " + name for name in networks) or "No active IPv4 adapters found") + "\n\nCreate your first rule by choosing an application and network.")
        create = box.addButton("Create first rule", QMessageBox.AcceptRole)
        box.addButton("Explore dashboard", QMessageBox.RejectRole)
        box.exec()
        self.settings.values["welcomed"] = True
        self.safe(self.settings.save)
        if box.clickedButton() is create:
            self.nav.setCurrentRow(1)
            self.add_rule()
