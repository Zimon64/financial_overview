import os
import pandas as pd
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


def load_csv(file_name):
    if not os.path.exists(file_name):
        create_csv(file_name)
    df = pd.read_csv(file_name, header=None, na_filter=False)  # na_filter=False verhindert NaN-Werte
    return df.fillna('').values.tolist()  # Fülle NaN-Werte mit leeren Strings


def save_csv(file_name, data):
    df = pd.DataFrame(data)
    df.fillna('', inplace=True)
    df.to_csv(file_name, index=False, header=False)


def create_csv(file_name):
    with open(file_name, 'w', newline='') as file:
        pass


# extra window for custom subscriptions and fixed income
class SecondWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Fixe Ausgaben')
        self.file_name = os.path.join('csv', 'fixe_ausgabe.csv')
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