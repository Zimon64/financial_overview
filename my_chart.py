# my_chart.py
from PyQt6.QtCharts import QChart, QPieSeries, QPieSlice
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import QLabel


class MyChart(QChart):
    def __init__(self, data, parent=None):
        super(MyChart, self).__init__(parent)
        self._data = data

        self.legend().hide()
        self.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.series = QPieSeries()
        self.series.setHoleSize(0.35)

        self.set_series()

        self.setBackgroundBrush(QBrush(QColor(45, 45, 45)))

        self.addSeries(self.series)

        self.title_label = QLabel(parent)
        self.title_label.setStyleSheet('color: white; background-color: rgba(0, 0, 0, 0);')
        self.title_label.move(10, 10)

    def set_series(self):
        for item in self._data:
            slice_ = QPieSlice(item['name'], item['value'])
            slice_.setLabelVisible()
            slice_.setColor(item['color'])
            slice_.setLabelBrush(item['color'])
            self.series.append(slice_)

            label_color = 'white' if slice_.percentage() > 0.1 else 'black'
            label = f"{slice_.label()} - {round(slice_.percentage() * 100, 2)}%"
            slice_.setLabel(label)

    def set_title_text(self, text):
        self.title_label.setText(text)
        self.title_label.adjustSize()
        self.title_label.show()
