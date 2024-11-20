# data_handler.py
import csv
import os
import chardet
from datetime import datetime
from PyQt6.QtWidgets import QTableWidget


def save_to_csv(tab_widget, headers, base_filename):
    for i in range(tab_widget.count()):
        tab = tab_widget.widget(i)
        if isinstance(tab, QTableWidget):
            sheet_name = tab_widget.tabText(i)
            file_path = f'{base_filename}_{sheet_name}.csv'
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                for row in range(tab.rowCount()):
                    row_data = []
                    for column in range(tab.columnCount()):
                        item = tab.item(row, column)
                        data = item.text() if item else ''
                        row_data.append(data)
                    writer.writerow(row_data)


import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding']

def load_from_csv(base_filename):
    tab_data = []
    csv_files = [f for f in os.listdir() if f.startswith(base_filename) and f.endswith('.csv')]

    csv_files.sort(key=lambda x: datetime.strptime(x.replace(base_filename + '_', '').replace('.csv', ''), '%B %Y'),
                   reverse=True)

    for csv_file in csv_files:
        sheet_name = os.path.splitext(csv_file)[0].replace(base_filename + '_', '')
        encoding = detect_encoding(csv_file)

        with open(csv_file, mode='r', newline='', encoding=encoding) as file:
            reader = csv.reader(file)
            headers = next(reader, [])
            data = [row for row in reader]

        tab_data.append((sheet_name, headers, data))

    return tab_data

