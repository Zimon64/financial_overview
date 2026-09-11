import os
import csv
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCharts import QBarSet, QBarSeries, QChart, QChartView, QBarCategoryAxis, QValueAxis
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
from PyQt6.QtCore import Qt


class SimpleBarChart(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Expenses during the month")
        self.setGeometry(0, 0, 800, 420)

        file_path = 'financials_October 2024.csv'
        self.categories = self.extract_unique_names_from_csv(file_path)
        summed_expenses = self.sum_of_unique_names(file_path)
        max_value_expenses = self.max_expenses_value(file_path)

        # Erstelle ein Dictionary für die Summen der Ausgaben
        expense_dict = dict(zip(self.categories, summed_expenses))

        # Sortiere die Kategorien alphabetisch und hole die zugehörigen Ausgaben
        sorted_categories = sorted(expense_dict.keys())
        sorted_expenses = [expense_dict[category] for category in sorted_categories]

        chart = QChart()
        bar_set = QBarSet("Einzelne Ausgaben")
        bar_set.append(sorted_expenses)

        series = QBarSeries()
        series.append(bar_set)
        chart.addSeries(series)

        chart.setTitle("Expenses during the month")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # Erstelle die x-Achse und y-Achse
        axis_x = QBarCategoryAxis()
        axis_x.append(sorted_categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)  # Hinzufügen der x-Achse

        axis_y = QValueAxis()
        axis_y.setRange(0, max_value_expenses + max_value_expenses * 0.1)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)  # Hinzufügen der y-Achse

        # set colors
        chart.setBackgroundBrush(QBrush(QColor(45, 45, 45)))
        chart.setTitleBrush(QBrush(QColor(255, 255, 255)))

        axis_x.setLabelsBrush(QBrush(QColor(255, 255, 255)))
        axis_y.setLabelsBrush(QBrush(QColor(255, 255, 255)))

        bar_set.setLabelBrush(QBrush(QColor(255, 255, 255)))

        # Verbinde die Achsen mit der Serie
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setCentralWidget(chart_view)

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
                    try:
                        expense = float(row[3])
                    except ValueError:
                        expense = 0
                    if name in sum_of_unique_expenses:
                        sum_of_unique_expenses[name] += expense
                    else:
                        sum_of_unique_expenses[name] = expense

        expense_list = [sum_of_unique_expenses[name] for name in self.categories]

        return expense_list

    def max_expenses_value(self, file_path):
        expense_list = self.sum_of_unique_names(file_path)
        if expense_list:
            max_value = max(expense_list)
            return max_value
        return 0

class ChartView(QChartView):
    def __init__(self, chart, categories, summed_expenses):
        super().__init__(chart)
        self.categories = categories
        self.summed_expenses = summed_expenses

    def draw_values_on_bars(self, painter):
        """Zeichnet die Werte über die Balken."""
        bar_series = self.chart().series()[0]  # QBarSeries-Objekt
        bar_set = bar_series.barSets()[0]  # Das erste QBarSet in der Serie

        # Für jede Kategorie die Balkenbreite ermitteln
        bar_width = self.chart().plotArea().width() / len(self.categories)
        bar_start_x = self.chart().plotArea().x()

        for i, value in enumerate(self.summed_expenses):
            bar_x = bar_start_x + i * bar_width
            bar_y = (self.chart().plotArea().y() + self.chart().plotArea().height()
                     * (1 - value / max(self.summed_expenses)))

            # Text über den Balken zeichnen
            painter.drawText(bar_x, bar_y - 5, f"{value:.2f}")

    def paintEvent(self, event):
        super().paintEvent(event)

        # Text auf die Balken zeichnen
        painter = QPainter(self.viewport())
        painter.setPen(QColor(255, 255, 255))  # Weißer Text
        font = QFont()
        font.setBold(True)
        painter.setFont(font)

        self.draw_values_on_bars(painter)
        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleBarChart()
    window.show()
    sys.exit(app.exec())
