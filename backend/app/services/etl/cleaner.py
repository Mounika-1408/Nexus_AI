import pandas as pd
def clean_categories(df):
    df["category"] = (
        df["category"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return df
def remove_duplicates(df):
    before = len(df)

    df = df.drop_duplicates()

    removed = before - len(df)

    return df, removed
def handle_missing_values(df):
    df["revenue"] = df["revenue"].fillna(0)
    df["expense"] = df["expense"].fillna(0)

    return df
def convert_numeric_columns(df):
    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce"
    )

    df["expense"] = pd.to_numeric(
        df["expense"],
        errors="coerce"
    )

    return df
def calculate_profit(df):
    df["profit"] = df["revenue"] - df["expense"]

    return df