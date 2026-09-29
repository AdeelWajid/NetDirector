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


def table(headers, stretch_column=None, column_widths=None):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.verticalHeader().hide()
    widget.setShowGrid(False)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SingleSelection)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    header = widget.horizontalHeader()
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setHighlightSections(False)
    widget.verticalHeader().setDefaultSectionSize(48)
    if stretch_column is not None or column_widths is not None:
        header.setSectionResizeMode(QHeaderView.Interactive)
        if isinstance(stretch_column, (list, tuple)):
            for col in stretch_column:
                header.setSectionResizeMode(col, QHeaderView.Stretch)
        elif stretch_column is not None:
            header.setSectionResizeMode(stretch_column, QHeaderView.Stretch)
        if column_widths:
            for col, width in column_widths.items():
                widget.setColumnWidth(col, width)
    else:
        header.setSectionResizeMode(QHeaderView.Stretch)
    return widget


def set_rows(widget, rows):
    selected = widget.currentRow()
    widget.setUpdatesEnabled(False)
    try:
        if widget.rowCount() != len(rows):
            widget.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, text in enumerate(row):
                text_str = str(text)
                item = widget.item(i, j)
                if item is None:
                    item = QTableWidgetItem(text_str)
                    item.setToolTip(text_str)
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    widget.setItem(i, j, item)
                else:
                    if item.text() != text_str:
                        item.setText(text_str)
                    if item.toolTip() != text_str:
                        item.setToolTip(text_str)
                    if item.textAlignment() != (Qt.AlignLeft | Qt.AlignVCenter):
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if 0 <= selected < len(rows):
            if widget.currentRow() != selected:
                widget.selectRow(selected)
    finally:
        widget.setUpdatesEnabled(True)
