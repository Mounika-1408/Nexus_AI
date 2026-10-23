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


def normalize_currencies(df):
    """
    Normalizes multi-currency transaction revenue and expenses to Base Currency (USD).
    Preserves original nominal revenue, expense, and currency code in:
    original_revenue, original_expense, and currency columns.
    Computes exchange_rate used for full auditability.
    """
    from app.services.currency_service import FX_RATES_TO_BASE, BASE_CURRENCY

    # Preserve original nominal values
    df["original_revenue"] = df["revenue"].copy()
    df["original_expense"] = df["expense"].copy()

    if "currency" in df.columns:
        df["currency"] = df["currency"].astype(str).str.strip().str.upper()
    else:
        df["currency"] = BASE_CURRENCY

    # Map exchange rate (rate is foreign units per 1.0 USD base)
    df["exchange_rate"] = df["currency"].map(FX_RATES_TO_BASE).fillna(1.0)

    # Normalize to Base Currency (USD)
    df["revenue"] = (df["original_revenue"] / df["exchange_rate"]).round(2)
    df["expense"] = (df["original_expense"] / df["exchange_rate"]).round(2)
    df["profit"] = (df["revenue"] - df["expense"]).round(2)

    return df