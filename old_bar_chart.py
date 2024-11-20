# bar_chart.py

import sys
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QChart, QChartView, QBarSet, QValueAxis
from PySide6.QtGui import QPainter, QBrush, QColor, QFont
from PySide6.QtCore import Qt

import csv


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(800, 420)

        file_path = 'financials_October 2024.csv'
        self.categories = self.extract_unique_names_from_csv(file_path)
        summed_expenses = self.sum_of_unique_names(file_path)
        max_value_expenses = self.max_expenses_value(file_path)

        # Erstelle ein Dictionary für die Summen der Ausgaben
        expense_dict = dict(zip(self.categories, summed_expenses))

        # Sortiere die Kategorien alphabetisch und hole die zugehörigen Ausgaben
        sorted_categories = sorted(expense_dict.keys())
        sorted_expenses = [expense_dict[category] for category in sorted_categories]

        self.set_values = QBarSet('Art der Ausgaben')
        self.set_values.append(sorted_expenses)

        self.series = QBarSeries()
        self.series.append(self.set_values)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle('Expenses during the month')
        self.chart.setAnimationOptions(QChart.SeriesAnimations)

        self.chart.setBackgroundBrush(QBrush(QColor(45, 45, 45)))

        # Kategorien für die x-Achse
        self.axisX = QBarCategoryAxis()
        self.axisX.append(sorted_categories)  # Hinzufügen der sortierten Kategorien
        self.axisX.setLabelsAngle(-45)  # Drehe die Labels um 45 Grad

        self.axisY = QValueAxis()
        self.axisY.setRange(0, round(max_value_expenses + 20, -1))

        # Achsen zuweisen
        self.chart.addAxis(self.axisX, Qt.AlignBottom)
        self.chart.addAxis(self.axisY, Qt.AlignLeft)
        self.series.attachAxis(self.axisX)
        self.series.attachAxis(self.axisY)

        # Verwende die ChartView-Klasse mit benutzerdefinierter Beschriftung
        self.chart_view = ChartView(self.chart, sorted_categories, sorted_expenses)  # Pass die sortierten Daten hier weiter
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        # Farben für Achsenbeschriftungen und Titel
        self.chart.axisX().setTitleBrush(QBrush(QColor(255, 255, 255)))
        self.chart.axisY().setTitleBrush(QBrush(QColor(255, 255, 255)))
        self.chart.axisX().setLabelsBrush(QBrush(QColor(255, 255, 255)))
        self.chart.axisY().setLabelsBrush(QBrush(QColor(255, 255, 255)))

        # Konfiguriere die Legende und den Titel
        self.chart.legend().setBrush(QBrush(QColor(255, 255, 255)))
        self.chart.setTitleBrush(QBrush(QColor(255, 255, 255)))

        self.setCentralWidget(self.chart_view)


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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())