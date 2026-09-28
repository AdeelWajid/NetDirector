from qt_compat.QtGui import QColor, QPalette


def system_is_dark(app):
    if hasattr(app.styleHints(), "colorScheme"):
        return app.styleHints().colorScheme().name == "Dark"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            return winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
    except (ImportError, OSError):
        return False


def watch_system_theme(app, callback):
    hints = app.styleHints()
    if hasattr(hints, "colorSchemeChanged"):
        hints.colorSchemeChanged.connect(lambda _: callback())
    else:
        # Qt 5 has no colorSchemeChanged signal. Keep System mode functional.
        from qt_compat.QtCore import QTimer
        previous = [system_is_dark(app)]
        def check():
            current = system_is_dark(app)
            if current != previous[0]:
                previous[0] = current
                callback()
        app.theme_timer = QTimer(app)
        app.theme_timer.timeout.connect(check)
        app.theme_timer.start(10000)


def apply_theme(app, choice="system", compact=False):
    dark = choice == "dark" or (choice == "system" and system_is_dark(app))
    app.setProperty("netdirectorDark", dark)
    bg, card, text, muted, border, hover = ("#222a46", "#2b3553", "#f4f0fa", "#aaaec5", "#3c4563", "#374161") if dark else ("#eeedf6", "#fcfaff", "#34324c", "#79758f", "#ddd9eb", "#e9e3f4")
    card_end = "#252e4b" if dark else "#f2eef9"
    palette = QPalette()
    for role, color in [(QPalette.Window, bg), (QPalette.Base, card), (QPalette.Text, text),
                        (QPalette.WindowText, text), (QPalette.Button, card), (QPalette.ButtonText, text),
                        (QPalette.Highlight, "#b66bcd"), (QPalette.HighlightedText, "#ffffff")]:
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    pad = 7 if compact else 11
    app.setStyleSheet(f"""
        QWidget {{ color: {text}; font-family: 'Segoe UI'; font-size: 10pt; }}
        QMainWindow, QDialog {{ background: {bg}; }}
        QLabel {{ background: transparent; }}
        QFrame#topbar {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #9882df, stop:0.48 #bb6fc9, stop:1 #eb4c9e); border: none; border-bottom-left-radius: 14px; border-bottom-right-radius: 14px; }}
        QFrame#topbar QLabel {{ color: #ffffff; }}
        QFrame#surface, QFrame#card {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {card}, stop:1 {card_end}); border: 1px solid {'#303a58' if dark else border}; border-radius: 16px; }}
        QLabel#title {{ font-size: 21pt; font-weight: 600; }}
        QLabel#subtitle, QLabel#muted {{ color: {muted}; font-size: 9pt; }}
        QLabel#eyebrow {{ color: {muted}; font-size: 8pt; letter-spacing: 2px; }}
        QLabel#section {{ font-size: 12pt; font-weight: 600; }}
        QLabel#metric {{ font-size: 27pt; font-family: 'Segoe UI Light'; }}
        QLabel#profileName {{ font-size: 21pt; font-family: 'Segoe UI Light'; }}
        QLabel#brand {{ font-size: 14pt; font-weight: 600; }}
        QLabel#brandSub {{ font-size: 8pt; color: #f2e2fa; letter-spacing: 1px; }}
        QLabel#pill {{ color: {'#d4c1eb' if dark else '#8861a8'}; background: {hover}; border-radius: 10px; padding: 7px 12px; font-size: 9pt; }}
        QLabel#online {{ color: {'#bddfcf' if dark else '#428365'}; font-size: 9pt; }}
        QPushButton {{ background: {card}; border: 1px solid {border}; border-radius: 9px; padding: {pad}px 15px; }}
        QPushButton:hover {{ background: {hover}; border-color: #b788d0; }}
        QPushButton:pressed {{ background: {border}; }}
        QPushButton:disabled {{ color: {muted}; }}
        QPushButton#primary, QPushButton#featuredTile {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #9c7bdb, stop:1 #e34f9e); color: white; border: 1px solid #b97acb; }}
        QPushButton#primary:hover, QPushButton#featuredTile:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ad8de8, stop:1 #ed67af); }}
        QPushButton#featuredTile QLabel {{ color: white; }}
        QPushButton#actionTile, QPushButton#featuredTile {{ border-radius: 14px; padding: 0; }}
        QPushButton#actionTile {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {card}, stop:1 {card_end}); border: 1px solid {'#333e5b' if dark else border}; }}
        QPushButton#actionTile:hover {{ border-color: #ae7aca; background: {hover}; }}
        QLabel#tileText {{ font-size: 9pt; }}
        QPushButton#navButton {{ border: 1px solid transparent; border-radius: 12px; background: transparent; padding: 8px; }}
        QPushButton#navButton:hover {{ background: rgba(255,255,255,25); }}
        QPushButton#navButton:checked {{ background: rgba(255,255,255,35); border: 1px solid rgba(255,255,255,55); }}
        QPushButton#profileSwitch {{ border-radius: 17px; padding: 6px 14px; color: {muted}; background: {hover}; }}
        QPushButton#profileSwitch:checked {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #a67add, stop:1 #ea55a6); color: white; border-color: #b885cf; }}
        QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{ background: {card}; border: 1px solid {border}; border-radius: 8px; padding: 9px; selection-background-color: #a774ce; }}
        QComboBox::drop-down {{ border: none; width: 25px; }}
        QComboBox QAbstractItemView {{ background: {card}; selection-background-color: {hover}; }}
        QTableWidget {{ background: {card}; alternate-background-color: {card_end}; border: 1px solid {border}; border-radius: 12px; gridline-color: {border}; selection-background-color: {hover}; selection-color: {text}; }}
        QHeaderView::section {{ background: {card}; color: {muted}; padding: 12px 8px; border: none; border-bottom: 1px solid {border}; font-weight: 400; }}
        QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {border}; }}
        QScrollArea, QScrollArea > QWidget > QWidget {{ border: none; background: transparent; }}
        QScrollBar:vertical {{ width: 7px; background: transparent; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {border}; border-radius: 3px; min-height: 30px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QCheckBox {{ spacing: 10px; padding: 5px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; }}
        QMenu {{ background: {card}; border: 1px solid {border}; padding: 5px; }}
        QMenu::item {{ padding: 8px 24px; }}
        QMenu::item:selected {{ background: {hover}; }}
        QStatusBar {{ background: {bg}; color: {muted}; font-size: 8pt; padding: 2px 18px; }}
        QProgressBar {{ border: none; background: {border}; max-height: 3px; }}
        QProgressBar::chunk {{ background: #cb6ebc; }}
        QToolTip {{ background: {card}; color: {text}; border: 1px solid {border}; padding: 6px; }}
        QTabWidget::pane {{ border: 1px solid {border}; border-radius: 8px; }}
        QTabBar::tab {{ background: {card}; color: {muted}; padding: 12px 20px; border: none; }}
        QTabBar::tab:selected {{ color: {text}; border-bottom: 2px solid #c77ac6; }}
    """)
