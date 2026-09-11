from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget
from PyQt6.QtCore import Qt


class ExpenseBarChart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.init_chart(data)

    def init_chart(self, data):
        bar_set = QBarSet('Ausgaben')
        for value in data.values():
            bar_set.append(value)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('Ausgaben pro Kategorie')
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        categories = list(data.keys())
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        layout = QVBoxLayout()
        layout.addWidget(chart_view)
        self.setLayout(layout)


def get_expenses_by_category(table_widget: QTableWidget) -> dict:
    expenses_by_category = {}

    for row in range(table_widget.rowCount()):
        category_item = table_widget.item(row, 4)
        expense_item = table_widget.item(row, 3)

        if category_item and expense_item:
            category = category_item.text()
            try:
                expense = float(expense_item.text())
            except ValueError:
                continue

            if category in expenses_by_category:
                expenses_by_category[category] += expense
            else:
                expenses_by_category[category] = expense

    return expenses_by_category
