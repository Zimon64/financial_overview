import os
import pandas as pd


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
    # Diese Funktion erstellt eine leere CSV-Datei, falls sie nicht existiert
    with open(file_name, 'w', newline='') as file:
        pass
