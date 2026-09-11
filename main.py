#!/usr/bin/env python3

import sys
import os

import chart_helpers

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
    QSizePolicy,
    QComboBox,
)
from PyQt6.QtCore import (
    Qt,
    QDate
)
from utils import calculate_column_sum, set_table_item_with_alignment
from ui_helpers import make_table_non_editable
from data_handler import save_to_csv
from second_window import SecondWindow
from custom_widgets import Worksheets
from tab_manager import TabManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.is_loading = True  # Blockiert Tab-Events während des Ladens
        self.bar_chart_view = None
        self.all_charts = False
        self.second_window = None
        self.headers = ['Einnahmen', 'Fixe Ausgaben', 'Geld zur Freien Verfügung', 'Betrag der Ausgaben',
                        'Art der Ausgabe', 'Datum']

        self.setWindowTitle('Finanzübersicht')

        # Strukturierte Initialisierung
        self._init_ui()
        self._init_connections()
        self._load_initial_data()

    def _init_ui(self):
        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 1. TABS (ganz oben)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tab Manager (erstellt die Tabs in self.tab_widget)
        self.tab_manager = TabManager(self)

        # 2. BALKENDIAGRAMM
        self.bar_chart_view = QChartView()
        self.chart_helper = chart_helpers.ChartHelper(self)
        layout.addWidget(self.bar_chart_view, stretch=3)

        # 3. TABELLE UND KREISDIAGRAMM (unten nebeneinander)
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(1)
        self.info_table.setHorizontalHeaderLabels(['Gesamte Finanzen'])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.info_table.setRowCount(3)
        self.info_table.setVerticalHeaderLabels(['Einnahmen', 'Ausgaben', 'Verfügbar'])
        self.info_table.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.info_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        make_table_non_editable(self.info_table)

        self.chart_view = QChartView()
        self.chart_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        chart_layout = QHBoxLayout()
        chart_layout.addWidget(self.info_table)
        chart_layout.addWidget(self.chart_view)

        self.bottom_container = QWidget()
        self.bottom_container.setLayout(chart_layout)
        layout.addWidget(self.bottom_container, stretch=2)

        # 4. COMBOBOX & EINFÜGEN-BEREICH
        self.combo_box = QComboBox()
        self.combo_box.addItems(['Fastfood', 'Restaurant', 'Wandern', 'Sprit', 'Auto', 'Einkaufen', 'Friseur',
                                 'Sonstiges'])

        self.insert_button = QPushButton('Einfügen')
        self.insert_button.setEnabled(False)

        self.monthly_conditions_change_button = QPushButton('Fixe Ausgaben/Einnahmen anpassen')
        self.monthly_conditions_change_button.setStyleSheet(
            'QPushButton { background-color: purple; } QPushButton:pressed { color: grey; }')

        insert_layout = QHBoxLayout()
        insert_layout.addWidget(self.combo_box)
        insert_layout.addWidget(self.insert_button)
        insert_layout.addWidget(self.monthly_conditions_change_button)
        layout.addLayout(insert_layout)

        # 5. UPDATE-BUTTONS
        update_button_layout = QHBoxLayout()

        self.update_button = QPushButton('&Update')
        self.update_button.setToolTip('Only press when "Only bar chart" was pressed before.')
        update_button_layout.addWidget(self.update_button)

        self.update_bar_chart_button = QPushButton('Only bar chart')
        self.update_bar_chart_button.setStyleSheet(
            'QPushButton { background-color: gray; } QPushButton:pressed { color: black; }')
        update_button_layout.addWidget(self.update_bar_chart_button)

        self.actual_chart_button = QPushButton('&Actual Month')
        update_button_layout.addWidget(self.actual_chart_button)

        self.all_tabs_chart_button = QPushButton('&All Months Chart')
        update_button_layout.addWidget(self.all_tabs_chart_button)

        layout.addLayout(update_button_layout)

        # 6. AKTIONS-BUTTONS (Löschen, Neu, Speichern)
        button_layout = QHBoxLayout()

        self.last_row_delete_button = QPushButton('&Delete Row')
        self.last_row_delete_button.setStyleSheet(
            'QPushButton { background-color: red; } QPushButton:pressed { color: grey; }')
        button_layout.addWidget(self.last_row_delete_button)

        self.clear_last_column_button = QPushButton('Inhalt letzte Zeile löschen')
        self.clear_last_column_button.setStyleSheet(
            'QPushButton { background-color: rgb(100, 0, 0); } QPushButton:pressed { color: grey; }')
        button_layout.addWidget(self.clear_last_column_button)

        self.new_row_button = QPushButton('&New Row')
        self.new_row_button.setStyleSheet(
            'QPushButton { background-color: rgb(0, 75, 0); } QPushButton:pressed { color: grey; }')
        button_layout.addWidget(self.new_row_button)

        self.save_all = QPushButton('&Save All')
        self.save_all.setStyleSheet('QPushButton { background-color: green; } QPushButton:pressed { color: grey; }')
        button_layout.addWidget(self.save_all)

        layout.addLayout(button_layout)

    def _init_connections(self):
        self.monthly_conditions_change_button.clicked.connect(self.change_fixed_conditions)
        self.insert_button.clicked.connect(self.insert_combobox_value)
        self.tab_widget.currentChanged.connect(self.tab_manager.on_tab_changed)

        self.update_button.clicked.connect(self.update_sum)
        self.update_bar_chart_button.clicked.connect(self.update_bar_chart)
        self.update_bar_chart_button.clicked.connect(self.save)
        self.actual_chart_button.clicked.connect(self.chart_helper.update_chart)
        self.all_tabs_chart_button.clicked.connect(self.chart_helper.all_chart)

        self.last_row_delete_button.clicked.connect(self.last_row_delete)
        self.clear_last_column_button.clicked.connect(self.clear_last_column)
        self.new_row_button.clicked.connect(self.new_row)
        self.save_all.clicked.connect(self.save)

    def _load_initial_data(self):
        self.tab_manager.load()
        self.load_and_calculate()
        self.load_all_tabs_financials()
        self.chart_helper.create_bar_chart()

        for i in range(self.tab_widget.count()):
            table_widget = self.tab_widget.widget(i)
            if isinstance(table_widget, Worksheets):
                table_widget.itemChanged.connect(self.on_item_change)

    def update_bar_chart(self):
        self.chart_helper.create_bar_chart()
        self.all_charts = True

    def get_current_file_path(self):
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index < 0:
            return ""
        sheet_name = self.tab_widget.tabText(current_tab_index)
        return os.path.join('csv', f"financials_{sheet_name}.csv")

    def update_sum(self):
        if self.all_charts:
            self.info_table.setVisible(True)
            self.chart_view.setVisible(True)
            self.all_charts = False

        self.load_and_calculate()
        self.load_all_tabs_financials()
        self.chart_helper.update_chart()
        self.chart_helper.create_bar_chart()

    def clear_last_column(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets) and current_table.columnCount() > 0:
            last_column_index = current_table.columnCount() - 1
            for row in range(current_table.rowCount()):
                if current_table.item(row, last_column_index) is not None:
                    current_table.item(row, last_column_index).setText('')

    def new_row(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            current_table.insertRow(current_table.rowCount())

    def last_row_delete(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets) and current_table.rowCount() > 0:
            current_table.removeRow(current_table.rowCount() - 1)

    def save(self):
        save_to_csv(self.tab_widget, self.headers, 'financials')

    def sheet_exists(self, sheet_name):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == sheet_name:
                return True
        return False

    def insert_combobox_value(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            selected_items = current_table.selectedItems()
            if selected_items:
                current_item = selected_items[0]
                if current_item.column() == 4:
                    selected_text = self.combo_box.currentText()
                    current_item.setText(selected_text)

    def load_and_calculate(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            sum_column_0 = calculate_column_sum(current_table, 0)
            sum_column_1 = calculate_column_sum(current_table, 1)
            sum_column_3 = calculate_column_sum(current_table, 3)

            dif = round(sum_column_0 - sum_column_1 - sum_column_3, 2)

            if current_table.rowCount() > 0:
                set_table_item_with_alignment(current_table, 0, 2, dif)

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

        dif = round(sum_column_0 - sum_column_1 - sum_column_3, 2)

        if self.info_table.rowCount() > 0:
            set_table_item_with_alignment(self.info_table, 0, 0, sum_column_0)
            set_table_item_with_alignment(self.info_table, 1, 0, round(sum_column_1, 2))
            set_table_item_with_alignment(self.info_table, 2, 0, dif)

    def on_item_change(self, item):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            if item.column() == 3:
                if item.text():
                    date_item = current_table.item(item.row(), 5)
                    if date_item is None or date_item.text() == '':
                        current_date = QDate.currentDate().toString("dd.MM.yyyy")
                        date_item = QTableWidgetItem(current_date)
                        current_table.setItem(item.row(), 5, date_item)

                # KORREKTUR: Bar Chart direkt nach Eingabe einer Zahl neu zeichnen
                self.save()
                self.chart_helper.create_bar_chart()

            if item.column() == 3:
                if item.text():
                    self.insert_button.setEnabled(True)
                else:
                    self.insert_button.setEnabled(False)
            else:
                self.insert_button.setEnabled(False)

    def change_fixed_conditions(self):
        self.second_window = SecondWindow()
        self.second_window.exec()

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