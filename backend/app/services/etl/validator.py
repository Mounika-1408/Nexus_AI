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