from qt_compat.QtCore import Qt
from qt_compat.QtWidgets import (QFrame, QVBoxLayout, QLabel, QPushButton, QTableWidget,
                             QHeaderView, QAbstractItemView, QTableWidgetItem)


def label(text, kind=""):
    widget = QLabel(text)
    widget.setObjectName(kind)
    widget.setWordWrap(kind not in {"section", "title", "brand", "brandSub", "eyebrow"})
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


def card(title, value, detail):
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.addWidget(label(title, "muted"))
    layout.addWidget(label(value, "metric"))
    layout.addWidget(label(detail, "muted"))
    return frame


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.verticalHeader().hide()
    widget.setShowGrid(False)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    widget.verticalHeader().setDefaultSectionSize(58)
    return widget


def set_rows(widget, rows):
    selected = widget.currentRow()
    widget.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, text in enumerate(row):
            item = QTableWidgetItem(str(text))
            item.setToolTip(str(text))
            widget.setItem(i, j, item)
    if 0 <= selected < len(rows):
        widget.selectRow(selected)
