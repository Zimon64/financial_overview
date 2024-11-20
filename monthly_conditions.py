# monthly_conditions.py
import csv
import os.path

csv_file = 'fixe_ausgabe.csv'


def create_empty_csv():
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)


def read_expense_amount_from_csv():
    if not os.path.exists(csv_file):
        create_empty_csv()

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)

        fixed_income = []
        fixed_expenses = []
        monthly_expenses = {}

        headers = ['Einkommen', 'Betrag(Einkommen)', 'jeden Monat', 'Betrag(jeden Monat)', 'January', 'Betrag(Januar)',
                   'February', 'Betrag(Februar)', 'March', 'Betrag(Maerz)', 'April', 'Betrag(April)', 'May',
                   'Betrag(Mai)', 'June', 'Betrag(Juni)', 'July', 'Betrag(Juli)', 'August', 'Betrag(August)',
                   'September', 'Betrag(September)', 'October', 'Betrag(Oktober)', 'November', 'Betrag(November)',
                   'December', 'Betrag(Dezember)']

        for row in reader:
            if row[0]:
                fixed_income.append((row[0], float(row[1])))

            if row[2]:
                fixed_expenses.append((row[2], float(row[3])))

            for i in range(4, len(row) - 1, 2):
                month = headers[i]
                if row[i]:
                    if month not in monthly_expenses:
                        monthly_expenses[month] = []
                    monthly_expenses[month].append((row[i], float(row[i + 1])))

        # print("Monate in monthly_expenses:")
        # for month in monthly_expenses:
        #     print(month)

        return fixed_income, fixed_expenses, monthly_expenses


def get_fixed_income_and_expenses():
    fixed_income, fixed_expenses, _ = read_expense_amount_from_csv()
    return fixed_income, fixed_expenses


def get_monthly_conditions(sheet_month):
    fixed_income, fixed_expenses, monthly_expenses = read_expense_amount_from_csv()

    special_expenses = monthly_expenses.get(sheet_month, [])

    row_count = len(fixed_expenses) + len(special_expenses)

    monthly_conditions = {
        'row_count': row_count,
        'column_count': 4,
        'special_expenses': special_expenses,
    }

    return monthly_conditions


# only debugging
def display_monthly_data(sheet_month):
    fixed_income, fixed_expenses = get_fixed_income_and_expenses()
    monthly_conditions = get_monthly_conditions(sheet_month)

    print(f"Monat: {sheet_month}")
    print("\nFixe Einnahmen:")
    for income in fixed_income:
        print(f"- {income[0]}: {income[1]:.2f} EUR")

    print("\nFixe Ausgaben:")
    for expense in fixed_expenses:
        print(f"- {expense[0]}: {expense[1]:.2f} EUR")

    print("\nBesondere Ausgaben für diesen Monat:")
    if monthly_conditions['special_expenses']:
        for special_expense in monthly_conditions['special_expenses']:
            print(f"- {special_expense[0]}: {special_expense[1]:.2f} EUR")
    else:
        print("Keine besonderen Ausgaben für diesen Monat.")

    print(f"\nGesamtanzahl der Zeilen für diesen Monat: {monthly_conditions['row_count']}")
    print(f"Anzahl der Spalten: {monthly_conditions['column_count']}")


# Beispielaufruf
# monat = 'October'
# display_monthly_data(monat)
