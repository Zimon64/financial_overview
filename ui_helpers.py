# ui_helpers.py
from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtCore import Qt


def make_table_non_editable(table):
    if isinstance(table, QTableWidget):
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
