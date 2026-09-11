import os
import csv

from PyQt6.QtCharts import QChartView, QChart, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtCore import Qt

from my_chart import MyChart
from custom_widgets import Worksheets

class ChartHelper:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tab_widget = main_window.tab_widget

    def create_bar_chart(self):
        current_table = self.tab_widget.currentWidget()
        sum_of_unique_expenses = {}

        if isinstance(current_table, Worksheets):
            for row in range(current_table.rowCount()):
                cat_item = current_table.item(row, 4)
                val_item = current_table.item(row, 3)

                if cat_item and val_item and cat_item.text().strip() != "":
                    category = cat_item.text().strip()
                    try:
                        expense = float(val_item.text())
                    except ValueError:
                        expense = 0.0
                    sum_of_unique_expenses[category] = sum_of_unique_expenses.get(category, 0.0) + expense

        sorted_categories = sorted(sum_of_unique_expenses.keys())
        sorted_expenses = [sum_of_unique_expenses[cat] for cat in sorted_categories]

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

        # Ersetzt das alte Balkendiagramm im Layout des Hauptfensters
        main_layout = self.main_window.centralWidget().layout()
        if getattr(self.main_window, 'bar_chart_view', None) is not None:
            main_layout.replaceWidget(self.main_window.bar_chart_view, new_chart_view)
            self.main_window.bar_chart_view.deleteLater()
        else:
            main_layout.addWidget(new_chart_view)

        self.main_window.bar_chart_view = new_chart_view

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

            self.main_window.chart_view.setChart(chart)

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

        self.main_window.chart_view.setChart(chart)
