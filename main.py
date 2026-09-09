#!/usr/bin/env python3
# main.py

import sys
import csv
import os
from math import ceil

from PyQt6.QtCharts import (
    QChartView,
    QChart,
    QBarSet,
    QBarSeries,
    QBarCategoryAxis,
    QValueAxis
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHeaderView,
    QHBoxLayout,
    QMainWindow,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QCheckBox,
    QLabel,
    QTabBar,
    QSizePolicy,
    QComboBox,
    QMessageBox
)
from PyQt6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractTableModel,
    QDate
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont

from my_chart import MyChart
from monthly_conditions import get_monthly_conditions, get_fixed_income_and_expenses
from utils import calculate_column_sum, set_table_item_with_alignment
from ui_helpers import make_table_non_editable
from data_handler import save_to_csv, load_from_csv
from second_window import load_csv, save_csv


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.is_loading = True  # Blockiert Tab-Events während des Ladens
        self.bar_chart_view = None
        self.all_charts = False

        self.second_window = None
        self.setWindowTitle('Finanzübersicht')
        self.headers = ['Einnahmen', 'Fixe Ausgaben', 'Geld zur Freien Verfügung', 'Betrag der Ausgaben',
                        'Art der Ausgabe', 'Datum']

        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 1. TABS (ganz oben)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 2. BALKENDIAGRAMM (großer Platzhalter in der Mitte)
        self.bar_chart_view = QChartView()
        # Stretch=3 gibt dem Balkendiagramm den Hauptplatz im Fenster!
        layout.addWidget(self.bar_chart_view, stretch=3)

        # 3. TABELLE UND KREISDIAGRAMM (unten nebeneinander, kompakt)
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(1)
        self.info_table.setHorizontalHeaderLabels(['Gesamte Finanzen'])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.info_table.setRowCount(3)
        self.info_table.setVerticalHeaderLabels(['Einnahmen', 'Ausgaben', 'Verfügbar'])
        self.info_table.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.info_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Kreisdiagramm (chart_view) kompakt halten
        self.chart_view = QChartView()
        self.chart_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Unteres horizontales Layout für Tabelle & Kreisdiagramm
        self.chart_layout = QHBoxLayout()
        self.chart_layout.addWidget(self.info_table)
        self.chart_layout.addWidget(self.chart_view)

        # NEU: Ein Container-Widget für den gesamten unteren Bereich erstellen
        self.bottom_container = QWidget()
        self.bottom_container.setLayout(self.chart_layout)

        # Füge das Container-Widget statt des Layouts direkt hinzu
        layout.addWidget(self.bottom_container, stretch=2)

        make_table_non_editable(self.info_table)

        # Auswahl für Spalte 5
        self.combo_box = QComboBox()
        self.combo_box.addItems(['Fastfood', 'Restaurant', 'Wandern', 'Sprit', 'Auto', 'Einkaufen', 'Friseur',
                                 'Sonstiges'])

        # einfügen der Arten von Ausgaben
        self.insert_button = QPushButton('Einfügen')
        self.insert_button.setEnabled(False)

        # fixe Ausgaben anpassen
        self.monthly_conditions_change_button = QPushButton('Fixe Ausgaben/Einnahmen anpassen')
        self.monthly_conditions_change_button.setToolTip(
            'For automatically adding your fix in- and outcome for every year'
            'or custom month.')
        self.monthly_conditions_change_button.setStyleSheet('QPushButton {'
                                                            ' background-color: purple;'
                                                            '}'
                                                            'QPushButton:pressed {'
                                                            ' color: grey;'
                                                            '}')
        self.monthly_conditions_change_button.clicked.connect(self.change_fixed_conditions)

        insert_layout = QHBoxLayout()
        insert_layout.addWidget(self.combo_box)
        insert_layout.addWidget(self.insert_button)
        insert_layout.addWidget(self.monthly_conditions_change_button)
        layout.addLayout(insert_layout)

        self.insert_button.clicked.connect(self.insert_combobox_value)

        # Nur ein Event verbinden, damit es keine Mehrfach-Aufrufe gibt
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # update-Funktionen
        update_button_layout = QHBoxLayout()

        self.update_button = QPushButton('&Update')
        self.update_button.setToolTip('Only press when "Only bar chart" was pressed before.<br>'
                                      'Otherwise the programm will crash!')
        self.update_button.clicked.connect(self.update_sum)
        update_button_layout.addWidget(self.update_button)

        self.update_bar_chart_button = QPushButton('Only bar chart')
        self.update_bar_chart_button.setToolTip('If the bar chart in this window no longer displays the names, you can'
                                                ' use this option for better visibility or a broader overview.<br>'
                                                '(automatically saves the table)')
        self.update_bar_chart_button.setStyleSheet('QPushButton {'
                                                   ' background-color: gray;'
                                                   '}'
                                                   'QPushButton:pressed {'
                                                   ' color: black;'
                                                   '}')
        self.update_bar_chart_button.clicked.connect(self.update_bar_chart)
        self.update_bar_chart_button.clicked.connect(self.save)
        update_button_layout.addWidget(self.update_bar_chart_button)

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

        # leste Spalte löschen
        self.clear_last_column_button = QPushButton('Inhalt letzte Zeile löschen')
        self.clear_last_column_button.setStyleSheet('QPushButton {'
                                                    ' background-color: rgb(100, 0, 0);'
                                                    '}'
                                                    'QPushButton:pressed {'
                                                    ' color: grey;'
                                                    '}')
        self.clear_last_column_button.clicked.connect(self.clear_last_column)
        button_layout.addWidget(self.clear_last_column_button)

        # Button der neue Zeilen einfügt
        self.new_row_button = QPushButton('&New Row')
        self.new_row_button.setToolTip('Adds new Row in the table.')
        self.new_row_button.setStyleSheet('QPushButton {'
                                          ' background-color: rgb(0, 75, 0);'
                                          '}'
                                          'QPushButton:pressed {'
                                          ' color: grey;'
                                          '}')
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

        # Erstes Bar-Chart rendern
        self.create_bar_chart()

        for i in range(self.tab_widget.count()):
            table_widget = self.tab_widget.widget(i)
            if isinstance(table_widget, Worksheets):
                table_widget.itemChanged.connect(self.on_item_change)

    # Balkendiagramm für MainWindow
    def create_bar_chart(self):
        sorted_categories, sorted_expenses = self.get_chart_data_from_table()

        bar_set = QBarSet("Art der Ausgaben")
        bar_set.append(sorted_expenses)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)

        current_tab_index = self.tab_widget.currentIndex()
        sheet_name = self.tab_widget.tabText(current_tab_index) if current_tab_index >= 0 else ""
        chart.setTitle(f"Expenses - {sheet_name}")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QBrush(QColor(45, 45, 45)))

        axis_x = QBarCategoryAxis()
        axis_x.append(sorted_categories)
        axis_x.setLabelsAngle(-45)
        axis_x.setLabelsBrush(QBrush(QColor(255, 255, 255)))

        max_val = max(sorted_expenses) if sorted_expenses else 0
        axis_y = QValueAxis()
        axis_y.setRange(0, round(max_val + 20, -1) if max_val > 0 else 10)
        axis_y.setLabelsBrush(QBrush(QColor(255, 255, 255)))

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart.setTitleBrush(QBrush(QColor(255, 255, 255)))
        chart.legend().setBrush(QBrush(QColor(255, 255, 255)))

        new_chart_view = QChartView(chart)
        new_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Ersetzt das bestehende Bar Chart im Hauptlayout (oben in der Mitte)
        main_layout = self.centralWidget().layout()
        if getattr(self, 'bar_chart_view', None) is not None:
            main_layout.replaceWidget(self.bar_chart_view, new_chart_view)
            self.bar_chart_view.deleteLater()
        else:
            main_layout.addWidget(new_chart_view)

        self.bar_chart_view = new_chart_view

    def get_chart_data_from_table(self):
        current_table = self.tab_widget.currentWidget()
        sum_of_unique_expenses = {}

        # Prüfen, ob wirklich ein Worksheet-Tab geöffnet ist
        if isinstance(current_table, Worksheets):
            for row in range(current_table.rowCount()):
                cat_item = current_table.item(row, 4)  # Spalte 4: Art der Ausgabe
                val_item = current_table.item(row, 3)  # Spalte 3: Betrag

                # Nur verarbeiten, wenn in der Kategorie-Spalte auch etwas steht
                if cat_item and val_item and cat_item.text().strip() != "":
                    category = cat_item.text().strip()
                    try:
                        expense = float(val_item.text())
                    except ValueError:
                        expense = 0.0

                    # Werte aufsummieren
                    if category in sum_of_unique_expenses:
                        sum_of_unique_expenses[category] += expense
                    else:
                        sum_of_unique_expenses[category] = expense

        # Direkt alphabetisch sortieren für das Diagramm
        sorted_categories = sorted(sum_of_unique_expenses.keys())
        sorted_expenses = [sum_of_unique_expenses[cat] for cat in sorted_categories]

        return sorted_categories, sorted_expenses

    def update_bar_chart(self):
        self.create_bar_chart()
        self.all_charts = True

    def get_current_file_path(self):
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index < 0:
            return ""
        sheet_name = self.tab_widget.tabText(current_tab_index)
        return f"financials_{sheet_name}.csv"

    def extract_unique_names_from_csv(self, file_path):
        unique_names = set()
        if not os.path.exists(file_path):
            return []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader, None)
            for row in csvreader:
                if len(row) >= 5 and row[4]:
                    unique_names.add(row[4])
        return list(unique_names)

    def sum_of_unique_names(self, file_path):
        sum_of_unique_expenses = {}
        if not os.path.exists(file_path):
            return [], []

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader, None)

            for row in csvreader:
                if len(row) >= 5 and row[3]:
                    name = row[4]
                    try:
                        expense = float(row[3])
                    except ValueError:
                        expense = 0
                    if name in sum_of_unique_expenses:
                        sum_of_unique_expenses[name] += expense
                    else:
                        sum_of_unique_expenses[name] = expense

        categories = list(sum_of_unique_expenses.keys())
        expense_list = [sum_of_unique_expenses[name] for name in categories]

        # KORREKTUR: Reihenfolge korrigiert auf (categories, expense_list)
        return categories, expense_list

    def max_expenses_value(self, file_path):
        categories, expense_list = self.sum_of_unique_names(file_path)
        if expense_list:
            return max(expense_list)
        return 0

    def update_sum(self):
        if self.all_charts:
            self.info_table.setVisible(True)
            self.chart_view.setVisible(True)
            self.all_charts = False

        self.load_and_calculate()
        self.load_all_tabs_financials()
        self.update_chart()
        self.create_bar_chart()

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
        new_table.itemChanged.connect(self.on_item_change)

        self.tab_widget.insertTab(0, new_table, sheet_name)

        tab_button = TabButton(sheet_name)
        self.tab_widget.tabBar().setTabButton(0, QTabBar.ButtonPosition.LeftSide, tab_button)

        tab_button.checkbox.toggled.connect(
            lambda checked, index=0: self.close_tab(index) if checked else None)

        for row_index, (income_name, income_value) in enumerate(fixed_income):
            new_table.setItem(row_index, 0, QTableWidgetItem(str(income_value)))

        for row_index, (expense_name, expense_value) in enumerate(fixed_expenses):
            new_table.setItem(row_index, 1, QTableWidgetItem(str(expense_value)))

        for row_index, (expense_name, expense_value) in enumerate(special_expenses, start=len(fixed_expenses)):
            new_table.setItem(row_index, 1, QTableWidgetItem(str(expense_value)))

        save_to_csv(self.tab_widget, self.headers, 'financials')
        print("Saving data to csv...")
        self.load()

        self.update_chart()

    def clear_last_column(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets) and current_table.columnCount() > 0:
            last_column_index = current_table.columnCount() - 1
            for row in range(current_table.rowCount()):
                if current_table.item(row, last_column_index) is not None:
                    current_table.item(row, last_column_index).setText('')

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
        save_to_csv(self.tab_widget, self.headers, 'financials')

    def load(self):
        self.is_loading = True
        self.tab_widget.clear()

        tab_data = load_from_csv('financials')

        for sheet_name, headers, data in tab_data:
            num_rows = len(data)
            num_columns = len(headers)

            new_table = Worksheets(num_rows, num_columns)
            new_table.setHorizontalHeaderLabels(headers)

            new_table.itemChanged.connect(self.on_item_change)

            self.tab_widget.addTab(new_table, sheet_name)

            tab_button = TabButton(sheet_name)
            tab_index = self.tab_widget.indexOf(new_table)
            self.tab_widget.tabBar().setTabButton(tab_index, QTabBar.ButtonPosition.LeftSide, tab_button)

            tab_button.checkbox.toggled.connect(
                lambda checked, index=tab_index: self.close_tab(index) if checked else None)

            for row_index, row_data in enumerate(data):
                for col_index, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    new_table.setItem(row_index, col_index, item)

        current_date = QDate.currentDate()
        current_sheet_name = current_date.toString('MMMM yyyy')

        if not self.sheet_exists(current_sheet_name):
            print('Creating new file...')
            self.add_new_sheet()

        self.load_and_calculate()
        self.update_chart()
        self.is_loading = False

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

    def on_tab_changed(self):
        if getattr(self, 'is_loading', False):
            return

        # KORREKTUR: Jetzt wird das Bar-Chart bei Tab-Wechsel aktualisiert!
        self.create_bar_chart()
        self.update_chart()

        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            selected_items = current_table.selectedItems()

            if selected_items:
                current_item = selected_items[0]
                if current_item.column() == 4 and current_item.text().strip() != '':
                    self.insert_button.setEnabled(True)
                    return

            self.insert_button.setEnabled(False)

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
            chart.setTitle('Selected Month')

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
                self.create_bar_chart()

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


# extra window for custom subscriptions and fixed income
class SecondWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Fixe Ausgaben')
        self.file_name = 'fixe_ausgabe.csv'
        self.headers = ['Einkommen', 'Betrag(Einkommen)', 'jeden Monat', 'Betrag(jeden Monat)', 'Januar',
                        'Betrag(Januar)', 'Februar', 'Betrag(Februar)',
                        'Maerz', 'Betrag(Maerz)', 'April', 'Betrag(April)', 'Mai', 'Betrag(Mai)', 'Juni',
                        'Betrag(Juni)', 'Juli', 'Betrag(Juli)', 'August', 'Betrag(August)', 'September',
                        'Betrag(September)', 'Oktober', 'Betrag(Oktober)', 'November', 'Betrag(November)',
                        'Dezember', 'Betrag(Dezember)']
        self.data = load_csv(self.file_name)

        layout = QVBoxLayout()
        self.table = QTableWidget(len(self.data), len(self.headers))
        self.populate_table()
        layout.addWidget(self.table)

        self.add_row_button = QPushButton('New Row')
        self.add_row_button.setStyleSheet('QPushButton {'
                                          ' background-color: rgb(0, 100, 0);'
                                          '}'
                                          'QPushButton:pressed {'
                                          ' color: grey;'
                                          '}')
        self.add_row_button.clicked.connect(self.add_new_row)
        layout.addWidget(self.add_row_button)

        self.delete_row_button = QPushButton('Delete Last Row')
        self.delete_row_button.setStyleSheet('QPushButton {'
                                             ' background-color: rgb(100, 0, 0);'
                                             '}'
                                             'QPushButton:pressed {'
                                             ' color: grey;'
                                             '}')
        self.delete_row_button.clicked.connect(self.delete_last_row)
        layout.addWidget(self.delete_row_button)

        self.setLayout(layout)
        self.resize(1000, 400)

        self.show()

    def populate_table(self):
        self.table.setHorizontalHeaderLabels(self.headers)

        for row_idx, row_data in enumerate(self.data):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                if col_idx < 2:
                    item.setBackground(QColor(255, 230, 204))

                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

        for col in range(len(self.headers)):
            self.table.resizeColumnToContents(col)

    def closeEvent(self, event):
        self.save_table_data()
        event.accept()

    def save_table_data(self):
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                row_data.append(item.text() if item else '')
            data.append(row_data)

        save_csv(self.file_name, data)

    def add_new_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(''))

    def delete_last_row(self):
        if self.table.rowCount() > 0:
            self.table.removeRow(self.table.rowCount() - 1)
        else:
            QMessageBox.information(self, "Info", "There are no rows to delete.")


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