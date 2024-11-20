# main.py

import sys
import csv
import json
from typing import Dict, Any

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
    QComboBox, QGraphicsSimpleTextItem
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
from expense_bar_chart import ExpenseBarChart, get_expenses_by_category
from second_window import load_csv, save_csv
from bar_chart import ChartView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.second_window = None
        self.setWindowTitle('Finanzübersicht')
        self.headers = ['Einnahmen', 'Fixe Ausgaben', 'Geld zur Freien Verfügung', 'Grund',
                        'Art der Ausgabe', 'Datum']

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

        self.create_bar_chart()

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

        # Auswahl für Spalte 5
        self.combo_box = QComboBox()
        self.combo_box.addItems(['Fastfood', 'Restaurant', 'Wandern', 'Sprit', 'Auto', 'Einkaufen', 'Friseur',
                                 'Sonstiges'])

        # einfügen der Arten von Ausgaben
        self.insert_button = QPushButton('Einfügen')
        self.insert_button.setEnabled(False)

        # fixe Ausgaben anpassen
        self.monthly_conditions_change_button = QPushButton('Fixe Ausgaben/Einnahmen anpassen')
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

        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.tabBarClicked.connect(self.on_tab_changed)
        self.tab_widget.tabBarDoubleClicked.connect(self.on_tab_changed)

        # update-Funktionen
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

        for i in range(self.tab_widget.count()):
            table_widget = self.tab_widget.widget(i)
            if isinstance(table_widget, Worksheets):
                table_widget.itemChanged.connect(self.on_item_change)

    # Balkendiagramm für MainWindow
    def create_bar_chart(self):
        #Erstellen eines dynamischen Datasets
        file_path = 'financials_October 2024.csv'
        # file_path = self.get_current_file_path()
        categories, summed_expenses = self.sum_of_unique_names(file_path)

        # Erstelle ein Dictionary für die Summen der Ausgaben
        expense_dict = dict(zip(categories, summed_expenses))
        # print(f'Expense Dictionary: {expense_dict}')  # Debug-Output

        # Sortiere die Kategorien alphabetisch und hole die zugehörigen Ausgaben
        sorted_items = sorted(expense_dict.items())
        sorted_categories = [item[1] for item in sorted_items]  # Sortierte Kategorien
        sorted_expenses = [item[0] for item in sorted_items]  # Zuordnung der Ausgaben

        # Debug-Outputs zur Überprüfung der Werte
        # print(f'Sorted Categories: {sorted_categories}')  # Debug-Output
        # print(f'Sorted Expenses: {sorted_expenses}')  # Debug-Output

        # Create a bar set with the sorted expenses
        bar_set = QBarSet("Expenses")
        bar_set.append(sorted_expenses)  # Füge die sortierten Ausgaben hinzu
        # bar_set.append([30, 20, 30, 23, 20, 100, 69, 42, 25, 10, 3, 96, 55, 19, 60])

        # Create a bar series and add the bar set to it
        bar_series = QBarSeries()
        bar_series.append(bar_set)

        # Create a chart and add the bar series to it
        chart = QChart()
        chart.addSeries(bar_series)
        chart.setTitle("Monthly Expenses")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # X-Achse und Y-Achse erzeugen
        axis_x = QBarCategoryAxis()
        axis_x.append(sorted_categories)  # Setze die Labels der X-Achse
        axis_y = QValueAxis()  # Erstelle eine numerische Y-Achse

        # Setze die Achsen für das Diagramm
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        bar_series.attachAxis(axis_x)
        bar_series.attachAxis(axis_y)

        axis_x.setLabelsBrush(QBrush(QColor(255, 255, 255)))
        axis_x.setLabelsAngle(-90)

        axis_y.setLabelsBrush(QBrush(QColor(255, 255, 255)))

        # Create a chart view and set the chart
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # color of background and axis
        chart.setBackgroundBrush(QBrush(QColor(45, 45, 45)))
        chart.setTitleBrush(QBrush(QColor(255, 255, 255)))

        # # Beschriftung der Balken
        # for i, expense in enumerate(sorted_expenses):
        #     text_item = QGraphicsSimpleTextItem(f'{expense:.0f}')
        #     text_item.setFont(QFont('Arial', 10))
        #     text_item.setBrush(QBrush(QColor(255, 255, 255)))
        #
        #     bar_width = bar_series.barSets()[0].count()
        #     x_pos = chart.plotArea().left() + (i + 0.5) * (chart.plotArea().width() / bar_width)
        #     y_pos = chart.plotArea().top() + (1 - (expense / max(sorted_expenses))) * chart.plotArea().height()
        #
        #     text_item.setPos(x_pos, y_pos)
        #     chart.scene().addItem(text_item)

        # Add the chart view to your layout
        self.chart_layout.addWidget(chart_view)

    def get_current_file_path(self):
        current_tab_index = self.tab_widget.currentIndex()  # Aktuellen Tab-Index abrufen
        print(current_tab_index)
        sheet_name = self.tab_widget.tabText(current_tab_index)  # Tab-Text (Name des Blatts) abrufen
        print('hi')
        print(sheet_name)

        # Erzeuge den Dateipfad basierend auf dem Blattnamen
        file_path = f"financials_{sheet_name}.csv"  # Beispiel: financials_Oktober 2024.csv
        return file_path

    def extract_unique_names_from_csv(self, file_path):
        unique_names = set()
        with open(file_path, newline='', encoding='ISO-8859-1') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)
            for row in csvreader:
                if len(row) >= 5 and row[4]:
                    unique_names.add(row[4])
        return list(unique_names)

    def sum_of_unique_names(self, file_path):
        sum_of_unique_expenses = {}
        with open(file_path, newline='', encoding='ISO-8859-1') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)

            for row in csvreader:
                if len(row) >= 5 and row[3]:
                    name = row[4]
                    # print(name)
                    try:
                        expense = float(row[3])
                    except ValueError:
                        expense = 0
                    if name in sum_of_unique_expenses:
                        sum_of_unique_expenses[name] += expense
                        # print(sum_of_unique_expenses)
                    else:
                        sum_of_unique_expenses[name] = expense
                        # print(sum_of_unique_expenses)

        categories = list(sum_of_unique_expenses.keys())
        expense_list = [sum_of_unique_expenses[name] for name in categories]
        # print(expense_list)
        # print(sum_of_unique_expenses)

        # # für analyse des höchsten Wertes
        # field_names = sum_of_unique_expenses.keys()
        #
        # with open('ausgaben.csv', 'w') as csvfile:
        #     writer = csv.DictWriter(csvfile, fieldnames=field_names)
        #     writer.writeheader()
        #     writer.writerow(sum_of_unique_expenses)

        # max value of dic
        sorted_expenses = sorted(sum_of_unique_expenses.items(), key=lambda  x: x[1], reverse=True)

        n = 6
        nth_largest = sorted_expenses[n-1]
        print(f'{n}. größter Wert: {nth_largest}')

        return expense_list, categories

    def max_expenses_value(self, file_path):
        expense_list = self.sum_of_unique_names(file_path)
        if expense_list:
            max_value = max(expense_list)
            return max_value
        return 0

    def update_sum(self):
        self.load_and_calculate()

        self.load_all_tabs_financials()

        self.update_chart()

    def add_new_sheet(self):
        current_date = QDate.currentDate()
        # testcases
        # current_date = QDate(2024, 10, 25)
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

        self.tab_widget.addTab(new_table, sheet_name)

        tab_button = TabButton(sheet_name)
        tab_index = self.tab_widget.indexOf(new_table)
        self.tab_widget.tabBar().setTabButton(tab_index, QTabBar.ButtonPosition.LeftSide, tab_button)

        tab_button.checkbox.toggled.connect(
            lambda checked, index=tab_index: self.close_tab(index) if checked else None)

        save_to_csv(self.tab_widget, self.headers, 'financials')
        self.load()

        self.update_chart()

    def clear_last_column(self):
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets) and current_table.columnCount() > 0:
            last_column_index = current_table.columnCount() - 1  # Get the index of the last column
            for row in range(current_table.rowCount()):  # Iterate through each row
                if current_table.item(row, last_column_index) is not None:  # Check if the item exists
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
        # testcases
        # current_date = QDate(2024, 10, 25)
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
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            selected_items = current_table.selectedItems()

            # Prüfe, ob der aktuelle Wert in der Spalte 4 nicht leer ist
            if selected_items:
                current_item = selected_items[0]
                print(f'Row {current_item.row()}, Column {current_item.column()}')

                # Aktiviere die Einfügen-Taste, wenn ein Element in Spalte 4 existiert und nicht leer ist
                if current_item.column() == 4 and current_item.text().strip() != '':
                    self.insert_button.setEnabled(True)
                    return

            # Falls nichts gefunden wurde, deaktiviere die Taste
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
            print(f'Current table: {current_table}')

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

    def on_item_change(self, item):
        # print(f"Item changed: Row {item.row()}, Column {item.column()}, Text: {item.text()}")
        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            # prüfen, ob in 4. Spalte sich etw. geändert hat
            if item.column() == 3:
                if item.text():  # Check if the field is not empty
                    date_item = current_table.item(item.row(), 5)
                    if date_item is None or date_item.text() == '':  # Only set date if not already set
                        current_date = QDate.currentDate().toString("dd.MM.yyyy")
                        date_item = QTableWidgetItem(current_date)
                        current_table.setItem(item.row(), 5, date_item)

            if item.column() == 3:  # Note: Index is 3 because of 0-based indexing
                if item.text():  # Check if the cell in column 4 is not empty
                    self.insert_button.setEnabled(True)
                else:
                    self.insert_button.setEnabled(False)
            else:
                # Disable the button if another column's cell changes
                self.insert_button.setEnabled(False)

    def change_fixed_conditions(self):
        self.second_window = SecondWindow()  # Instanziiere das zweite Fenster
        self.second_window.exec()  # Zeige das zweite Fenster an


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
        # self.table = QTableWidget(len(self.data), len(self.data[0]) if self.data else 1)
        self.table = QTableWidget(len(self.data), len(self.headers))
        self.populate_table()
        layout.addWidget(self.table)

        self.add_row_button = QPushButton('Neue Zeile')
        self.add_row_button.clicked.connect(self.add_new_row)
        layout.addWidget(self.add_row_button)

        self.setLayout(layout)

        self.resize(1000, 400)

        self.show()

    def populate_table(self):
        self.table.setHorizontalHeaderLabels(self.headers)

        # self.table.setStyleSheet("background-color: transparent;")

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

        # Ursprünglich weil erste Zeile immer gelöscht wurde
        # empty_row = [''] * self.table.columnCount()
        # data.insert(0, empty_row)

        save_csv(self.file_name, data)

    def add_new_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(''))


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
