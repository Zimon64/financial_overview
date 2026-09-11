import os.path
import sys
import csv
from PyQt6.QtCharts import QChartView
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHeaderView,
    QHBoxLayout,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QCheckBox,
    QLabel,
    QTabBar,
    QSizePolicy
)
from PyQt6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractTableModel,
    QDate
)
from PyQt6.QtGui import QColor

from my_chart import MyChart
from monthly_conditions import get_monthly_conditions, get_fixed_income_and_expenses
from utils import calculate_column_sum, set_table_item_with_alignment


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Finanzübersicht')
        self.headers = ['Einnahmen', 'Fixe Ausgaben', 'Geld zur Freien Verfügung', 'Geld diesen Monat ausgegeben']

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # chart of actual tab
        self.chart_view = QChartView()
        layout.addWidget(self.chart_view)
        self.update_chart()

        self.chart_layout = QHBoxLayout()
        layout.addLayout(self.chart_layout)

        # chart of all tabs
        self.all_tabs_chart_view = QChartView()
        self.chart_layout.addWidget(self.chart_view)

        self.info_table = QTableWidget()
        self.info_table.setColumnCount(1)
        self.info_table.setHorizontalHeaderLabels(['Gesamte Finanzen'])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.info_table.setRowCount(3)
        self.info_table.setVerticalHeaderLabels(['Einnahmen', 'Ausgaben', 'Verfügbar'])
        self.info_table.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.info_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.chart_layout.addWidget(self.info_table)

        make_table_non_editable(self.info_table)

        self.all_chart()

        update_button_layout = QHBoxLayout()

        self.update_button = QPushButton('&Update')
        self.update_button.clicked.connect(self.update_sum)
        update_button_layout.addWidget(self.update_button)

        self.actual_chart_button = QPushButton('&Actual Month')
        self.actual_chart_button.clicked.connect(self.update_chart)
        update_button_layout.addWidget(self.actual_chart_button)

        self.all_tabs_chart_button = QPushButton('&All Months Chart')
        self.all_tabs_chart_button.clicked.connect(self.all_chart)
        update_button_layout.addWidget(self.all_tabs_chart_button)

        layout.addLayout(update_button_layout)

        button_layout = QHBoxLayout()

        # Button letzte Zeile löschen
        self.last_row_delete_button = QPushButton('&Delete Row')
        self.last_row_delete_button.setStyleSheet('QPushButton {'
                                                  ' background-color: red;'
                                                  '}'
                                                  'QPushButton:pressed {'
                                                  ' color: grey;'
                                                  '}')
        self.last_row_delete_button.clicked.connect(self.last_row_delete)
        button_layout.addWidget(self.last_row_delete_button)

        # Button der neue Zeilen einfügt
        self.new_row_button = QPushButton('&New Row')
        self.new_row_button.clicked.connect(self.new_row)
        button_layout.addWidget(self.new_row_button)

        # Button der aktuelle Zeilen & Einträge Speichert
        self.save_all = QPushButton('&Save All')
        self.save_all.setStyleSheet('QPushButton {'
                                    '   background-color: green;'
                                    '}'
                                    'QPushButton:pressed {'
                                    '   color: grey;'
                                    '}')
        self.save_all.clicked.connect(self.save)
        button_layout.addWidget(self.save_all)

        layout.addLayout(button_layout)

        self.load()
        self.load_and_calculate()
        self.load_all_tabs_financials()

    def update_sum(self):
        self.load_and_calculate()

        self.load_all_tabs_financials()

        self.update_chart()

    def add_new_sheet(self):
        current_date = QDate.currentDate()
        sheet_name = current_date.toString('MMMM yyyy')
        sheet_month = current_date.toString('MMMM')

        fixed_income, fixed_expenses = get_fixed_income_and_expenses()

        conditions = get_monthly_conditions(sheet_month)
        row_count = conditions['row_count']
        column_count = conditions['column_count']
        special_expenses = conditions['special_expenses']

        new_table = Worksheets(row_count, column_count)
        new_table.clear_table_contents()

        for row_index, (income_name, income_value) in enumerate(fixed_income):
            new_table.setItem(row_index, 0, QTableWidgetItem(str(income_value)))

        for row_index, (expense_name, expense_value) in enumerate(fixed_expenses):
            new_table.setItem(row_index, 1, QTableWidgetItem(str(expense_value)))

        for row_index, (expense_name, expense_value) in enumerate(special_expenses, start=6):
            new_table.setItem(row_index, 1, QTableWidgetItem(str(expense_value)))

        self.tab_widget.addTab(new_table, sheet_name)

        tab_button = TabButton(sheet_name)
        tab_index = self.tab_widget.indexOf(new_table)
        self.tab_widget.tabBar().setTabButton(tab_index, QTabBar.ButtonPosition.LeftSide, tab_button)

        tab_button.checkbox.toggled.connect(
            lambda checked, index=tab_index: self.close_tab(index) if checked else None)

        self.update_chart()

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def new_row(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            current_table.insertRow(current_table.rowCount())

    def last_row_delete(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets) and current_table.rowCount() > 0:
            current_table.removeRow(current_table.rowCount() - 1)

    def save(self):
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, Worksheets):
                sheet_name = self.tab_widget.tabText(i)
                file_path = f'{sheet_name}.csv'
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(self.headers)
                    for row in range(tab.rowCount()):
                        row_data = []
                        for column in range(tab.columnCount()):
                            item = tab.item(row, column)
                            data = item.text() if item else ''
                            row_data.append(data)
                        writer.writerow(row_data)

    def load(self):
        self.tab_widget.clear()

        # Alle CSV-Dateien im aktuellen Verzeichnis laden
        csv_files = [f for f in os.listdir() if f.endswith('.csv')]
        for csv_file in csv_files:
            sheet_name = os.path.splitext(csv_file)[0]

            # Erstellen eines neuen Arbeitsblatts
            with open(csv_file, mode='r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader, [])

                # Bestimmen der Anzahl der Zeilen und Spalten
                rows = []
                for row in reader:
                    rows.append(row)
                if rows:
                    num_rows = len(rows)
                    num_columns = len(rows[0])
                else:
                    num_rows = 6  # Setze eine Standardanzahl von Zeilen, falls keine Daten vorhanden sind
                    num_columns = len(
                        headers) if headers else 4  # Setze Standardanzahl von Spalten, falls keine Daten vorhanden sind

            new_table = Worksheets(num_rows, num_columns)  # Tabelle mit dynamischer Größe erstellen
            new_table.setHorizontalHeaderLabels(headers)
            self.tab_widget.addTab(new_table, sheet_name)

            # Add a custom tab button
            tab_button = TabButton(sheet_name)
            tab_index = self.tab_widget.indexOf(new_table)
            self.tab_widget.tabBar().setTabButton(tab_index, QTabBar.ButtonPosition.LeftSide, tab_button)

            # Connect the checkbox to the close tab function
            tab_button.checkbox.toggled.connect(
                lambda checked, index=tab_index: self.close_tab(index) if checked else None)

            # Daten in die Tabelle einfügen
            for row_index, row_data in enumerate(rows):
                if row_index < new_table.rowCount():
                    for col_index, data in enumerate(row_data):
                        if col_index < new_table.columnCount():
                            item = QTableWidgetItem(data)
                            new_table.setItem(row_index, col_index, item)

        current_date = QDate.currentDate()
        current_sheet_name = current_date.toString('MMMM yyyy')

        if not self.sheet_exists(current_sheet_name):
            self.add_new_sheet()

        self.load_and_calculate()
        self.update_chart()

    def sheet_exists(self, sheet_name):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == sheet_name:
                return True
        return False

    def load_and_calculate(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            sum_column_0 = calculate_column_sum(current_table, 0)
            sum_column_1 = calculate_column_sum(current_table, 1)
            sum_column_3 = calculate_column_sum(current_table, 3)

            dif = round(sum_column_0 - sum_column_1 - sum_column_3)

            if current_table.rowCount() > 0:
                set_table_item_with_alignment(current_table, 0, 2, dif)

            # print(f"Summe Spalte 0: {sum_column_0}")
            # print(f"Summe Spalte 1: {sum_column_1}")
            # print(f"Summe Spalte 3: {sum_column_3}")

    def load_all_tabs_financials(self):
        sum_column_0 = 0
        sum_column_1 = 0
        sum_column_3 = 0

        for i in range(self.tab_widget.count()):
            current_table = self.tab_widget.widget(i)

            if isinstance(current_table, Worksheets):
                sum_column_0 += calculate_column_sum(current_table, 0)
                sum_column_1 += calculate_column_sum(current_table, 1)
                sum_column_3 += calculate_column_sum(current_table, 3)

        dif = round(sum_column_0 - sum_column_1 - sum_column_3)

        if self.info_table.rowCount() > 0:
            set_table_item_with_alignment(self.info_table, 0, 0, sum_column_0)
            set_table_item_with_alignment(self.info_table, 1, 0, sum_column_1)
            set_table_item_with_alignment(self.info_table, 2, 0, dif)

    def update_chart(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            total_income = 0
            total_expenses = 0
            total_spent = 0

            for row in range(current_table.rowCount()):
                value_col_0 = current_table.item(row, 0).text() if current_table.item(row, 0) else '0'
                value_col_1 = current_table.item(row, 1).text() if current_table.item(row, 1) else '0'
                value_col_3 = current_table.item(row, 3).text() if current_table.item(row, 3) else '0'

                try:
                    total_income += float(value_col_0) if value_col_0 else 0
                    total_expenses += float(value_col_1) if value_col_1 else 0
                    total_spent += float(value_col_3) if value_col_3 else 0
                except ValueError:
                    continue

            total_available = total_income - total_expenses - total_spent

            chart_data = [
                {'name': 'Fixe Ausgaben', 'value': total_expenses, 'color': QColor('rosa')},
                {'name': 'Geld zur Freien Verfügung', 'value': total_available, 'color': QColor('green')},
                {'name': 'Zusätzliche Ausgaben', 'value': total_spent, 'color': QColor('red')},
            ]

            chart = MyChart(chart_data)
            chart.setTitle('Momentaner Monat')

            self.chart_view.setChart(chart)

    def all_chart(self):
        total_income = 0
        total_expenses = 0
        total_spent = 0

        for i in range(self.tab_widget.count()):
            current_table = self.tab_widget.widget(i)

            if isinstance(current_table, Worksheets):
                for row in range(current_table.rowCount()):
                    value_col_0 = current_table.item(row, 0).text() if current_table.item(row, 0) else '0'
                    value_col_1 = current_table.item(row, 1).text() if current_table.item(row, 1) else '0'
                    value_col_3 = current_table.item(row, 3).text() if current_table.item(row, 3) else '0'

                    try:
                        total_income += float(value_col_0) if value_col_0 else 0
                        total_expenses += float(value_col_1) if value_col_1 else 0
                        total_spent += float(value_col_3) if value_col_3 else 0
                    except ValueError:
                        continue

        total_available = total_income - total_expenses - total_spent

        chart_data = [
            {'name': 'Fixe Ausgaben', 'value': total_expenses, 'color': QColor('rosa')},
            {'name': 'Geld zur Freien Verfügung', 'value': total_available, 'color': QColor('green')},
            {'name': 'Zusätzliche Ausgaben', 'value': total_spent, 'color': QColor('red')},
        ]

        chart = MyChart(chart_data)
        chart.setTitle('Gesamte Übersicht')

        self.chart_view.setChart(chart)


class Worksheets(QTableWidget):
    def __init__(self, row_count, column_count, parent=None):
        super().__init__(row_count, column_count, parent)
        self.initialize_table()

    def initialize_table(self):
        self.setHorizontalHeaderLabels(['Einnahmen', 'Fixe Ausgaben', 'Geld zur Freien Verfügung',
                                        'Geld diesen Monat ausgegeben'])
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


def make_table_non_editable(table_widget):
    for row in range(table_widget.rowCount()):
        for col in range(table_widget.columnCount()):
            item = table_widget.item(row, col)
            if item is None:
                item = QTableWidgetItem()
                table_widget.setItem(row, col, item)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet('''
        QWidget {
            font-size: 17px
        }
    ''')

    window = MainWindow()
    window.showMaximized()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window...')
