from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QTabBar,
)
from PyQt6.QtCore import QDate
from monthly_conditions import get_monthly_conditions, get_fixed_income_and_expenses
from data_handler import save_to_csv, load_from_csv
from custom_widgets import Worksheets, TabButton


class TabManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tab_widget = main_window.tab_widget

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
        new_table.itemChanged.connect(self.main_window.on_item_change)

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

        save_to_csv(self.tab_widget, self.main_window.headers, 'financials')
        print("Saving data to csv...")
        self.load()

        self.main_window.chart_helper.update_chart()

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def load(self):
        self.is_loading = True
        self.tab_widget.clear()

        tab_data = load_from_csv('financials')

        for sheet_name, headers, data in tab_data:
            num_rows = len(data)
            num_columns = len(headers)

            new_table = Worksheets(num_rows, num_columns)
            new_table.setHorizontalHeaderLabels(headers)

            new_table.itemChanged.connect(self.main_window.on_item_change)

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

        self.main_window.load_and_calculate()
        self.main_window.chart_helper.update_chart()
        self.is_loading = False



    def sheet_exists(self, sheet_name):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == sheet_name:
                return True
        return False

    def on_tab_changed(self):
        if getattr(self, 'is_loading', False):
            return

        # KORREKTUR: Jetzt wird das Bar-Chart bei Tab-Wechsel aktualisiert!
        self.main_window.chart_helper.create_bar_chart()
        self.main_window.chart_helper.update_chart()

        current_table = self.tab_widget.currentWidget()
        if isinstance(current_table, Worksheets):
            selected_items = current_table.selectedItems()

            if selected_items:
                current_item = selected_items[0]
                if current_item.column() == 4 and current_item.text().strip() != '':
                    self.main_window.insert_button.setEnabled(True)
                    return

            self.main_window.insert_button.setEnabled(False)