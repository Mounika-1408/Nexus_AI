import pandas as pd


# --------------------------------------------------
# SCHEMA VALIDATION
# --------------------------------------------------

def validate_finance_schema(df):
    required_columns = [
        "transaction_id",
        "date",
        "marketplace",
        "category",
        "revenue",
        "expense",
        "currency",
        "payment_status"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    return missing_columns


# --------------------------------------------------
# DATE VALIDATION
# --------------------------------------------------

def validate_dates(df):
    parsed_dates = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_mask = parsed_dates.isna()

    invalid_rows = df[invalid_mask].copy()

    return invalid_rows


# --------------------------------------------------
# FINANCIAL VALIDATION
# --------------------------------------------------

def validate_finance_data(df):
    errors = []

    negative_expense = df[df["expense"] < 0]

    if not negative_expense.empty:
        errors.append({
            "type": "negative_expense",
            "count": len(negative_expense),
            "rows": negative_expense.index.tolist(),
            "values": negative_expense["expense"].tolist()
        })

    negative_revenue = df[df["revenue"] < 0]

    if not negative_revenue.empty:
        errors.append({
            "type": "negative_revenue",
            "count": len(negative_revenue),
            "rows": negative_revenue.index.tolist(),
            "values": negative_revenue["revenue"].tolist()
        })

    return errors


# --------------------------------------------------
# REMOVE INVALID FINANCIAL ROWS
# --------------------------------------------------

def remove_invalid_finance_rows(df):

    invalid_mask = (
        (df["revenue"] < 0) |
        (df["expense"] < 0)
    )

    invalid_rows = df[invalid_mask].copy()

    clean_df = df[~invalid_mask].copy()

    return clean_df, invalid_rows


# --------------------------------------------------
# REMOVE INVALID DATE ROWS
# --------------------------------------------------

def remove_invalid_date_rows(df):

    parsed_dates = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    invalid_mask = parsed_dates.isna()

    invalid_rows = df[invalid_mask].copy()

    clean_df = df[~invalid_mask].copy()

    clean_df = clean_df.copy()

    clean_df["date"] = parsed_dates[~invalid_mask].dt.strftime(
        "%Y-%m-%d"
    )

    return clean_df, invalid_rows


# --------------------------------------------------
# CURRENCY VALIDATION
# --------------------------------------------------

def validate_currency_data(df):
    """
    Validate that transactions specify a recognized and supported currency code.
    Identifies rows with missing, null, or unsupported currencies.
    """
    from app.services.currency_service import is_supported_currency

    if "currency" not in df.columns:
        return [{"type": "missing_currency_column", "count": len(df), "rows": df.index.tolist()}]

    errors = []
    unsupported_mask = ~df["currency"].apply(is_supported_currency)
    unsupported_rows = df[unsupported_mask]

    if not unsupported_rows.empty:
        errors.append({
            "type": "invalid_or_unsupported_currency",
            "count": len(unsupported_rows),
            "rows": unsupported_rows.index.tolist(),
            "values": unsupported_rows["currency"].tolist()
        })

    return errors


def remove_invalid_currency_rows(df):
    """
    Exclude records with missing or unsupported currencies so financial aggregation
    is strictly calculated using verified exchange rates.
    """
    from app.services.currency_service import is_supported_currency

    if "currency" not in df.columns:
        return df.iloc[0:0].copy(), df.copy()

    valid_mask = df["currency"].apply(is_supported_currency)
    invalid_rows = df[~valid_mask].copy()
    clean_df = df[valid_mask].copy()

    # Standardize currency column to uppercase stripped string
    clean_df["currency"] = clean_df["currency"].astype(str).str.strip().str.upper()

    return clean_df, invalid_rows