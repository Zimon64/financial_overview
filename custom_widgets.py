from PyQt6.QtWidgets import (
    QWidget,
    QHeaderView,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QLabel,
)
from PyQt6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractTableModel,
)

class Worksheets(QTableWidget):
    def __init__(self, row_count, column_count, parent=None):
        super().__init__(row_count, column_count, parent)
        self.initialize_table()

    def initialize_table(self):
        self.setHorizontalHeaderLabels(['Einnahmen', 'Fixe Ausgaben', 'Geld zur Freien Verfügung',
                                        'Geld diesen Monat ausgegeben', 'Art der Ausgabe', 'Datum'])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def clear_table_contents(self):
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                self.setItem(row, column, QTableWidgetItem(''))


class TableModel(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return self._data[index.row()][index.column()]
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


class TabButton(QWidget):
    def __init__(self, tab_name, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.lable = QLabel(tab_name)
        self.checkbox = QCheckBox()
        layout.addWidget(self.checkbox)
        self.setLayout(layout)