import pandas as pd


def remove_nan(file_name):
    df = pd.read_csv(file_name)

    df_cleaned = df.fillna('')
    df_cleaned.to_csv(file_name, index=False, header=False)


remove_nan('fixe_ausgabe.csv')
