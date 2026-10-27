import pandas as pd


def clean_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize categories to lowercase and handle null/empty categories gracefully (D2 fix).
    """
    if "category" in df.columns:
        df["category"] = df["category"].fillna("uncategorized")
        df["category"] = df["category"].astype(str).str.strip().str.lower()
        df.loc[df["category"].isin(["nan", "none", "", "null"]), "category"] = "uncategorized"
    return df


def remove_duplicates(df: pd.DataFrame):
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    return df, removed


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce non-numeric revenue and expense to NaN so they can be flagged and dropped by validator (D2 fix).
    Cleans currency symbols, thousand-separators, and stray characters cleanly.
    """
    for col in ["revenue", "expense"]:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                # Remove currency symbols and thousand separators, retaining digits, decimal, and minus
                cleaned = df[col].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'none', 'null'], float('nan'))
                df[col] = pd.to_numeric(cleaned, errors="coerce")
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Do not silently convert non-numeric revenue or expense to 0 (D2 fix).
    Invalid non-numeric values remain NaN to be filtered during financial validation.
    """
    return df


def calculate_profit(df: pd.DataFrame) -> pd.DataFrame:
    df["profit"] = df["revenue"] - df["expense"]
    return df


def normalize_currencies(df: pd.DataFrame) -> pd.DataFrame:
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