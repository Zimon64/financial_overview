from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt


def calculate_column_sum(table, column):
    total = 0
    for row in range(table.rowCount()):
        value = table.item(row, column).text() if table.item(row, column) else '0'
        try:
            total += float(value)
        except ValueError:
            continue
    return total


def set_table_item_with_alignment(table, row, col, value, alignment=Qt.AlignmentFlag.AlignCenter):
    item = QTableWidgetItem(str(value))
    item.setTextAlignment(alignment)
    table.setItem(row, col, item)
