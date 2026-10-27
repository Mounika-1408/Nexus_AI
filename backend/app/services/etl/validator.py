import pandas as pd


from typing import List, Dict

# --------------------------------------------------
# COLUMN ALIASES & CANONICAL SCHEMA DEFINITION
# --------------------------------------------------

REQUIRED_COLUMNS = ["date", "revenue"]

STANDARD_COLUMNS = [
    "transaction_id",
    "date",
    "marketplace",
    "category",
    "revenue",
    "expense",
    "currency",
    "payment_status"
]

COLUMN_ALIASES: Dict[str, str] = {
    # date aliases
    "transaction_date": "date",
    "txn_date": "date",
    "order_date": "date",
    "invoice_date": "date",
    "created_at": "date",
    "day": "date",
    "timestamp": "date",
    # revenue aliases
    "sales": "revenue",
    "total_revenue": "revenue",
    "gross_revenue": "revenue",
    "net_sales": "revenue",
    "gross_sales": "revenue",
    "income": "revenue",
    "turnover": "revenue",
    "amount": "revenue",
    # expense aliases
    "expenses": "expense",
    "cost": "expense",
    "costs": "expense",
    "total_expenses": "expense",
    "total_expense": "expense",
    "total_cost": "expense",
    "expenditure": "expense",
    "spending": "expense",
    # profit aliases
    "net_profit": "profit",
    "net_income": "profit",
    "margin": "profit",
    # category aliases
    "product_category": "category",
    "item_category": "category",
    "department": "category",
    "segment": "category",
    "type": "category",
    # currency aliases
    "curr": "currency",
    "cur": "currency",
    "currency_code": "currency",
    # transaction_id aliases
    "txn_id": "transaction_id",
    "id": "transaction_id",
    "order_id": "transaction_id",
    "invoice_id": "transaction_id",
    "order_number": "transaction_id",
    # marketplace aliases
    "channel": "marketplace",
    "source": "marketplace",
    "platform": "marketplace",
    "store": "marketplace",
    # payment_status aliases
    "status": "payment_status",
    "payment_state": "payment_status",
    "order_status": "payment_status",
}


def standardize_finance_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame columns and fill safe defaults for robust ETL ingestion:
    - Strips whitespace and BOM (\ufeff), lowercases column names.
    - Maps common aliases (e.g., 'expenses' -> 'expense', 'sales' -> 'revenue').
    - Fills default values for optional columns:
      * expense: if missing, calculated as revenue - profit if profit exists, else 0.0
      * profit: calculated as revenue - expense if not present
      * category: 'general'
      * currency: 'USD'
      * marketplace: 'Direct'
      * payment_status: 'completed'
      * transaction_id: preserved if present, else empty string
    """
    df = df.copy()

    # 1. Normalize column headers
    cleaned_cols = {}
    for col in df.columns:
        clean_col = str(col).strip().lstrip('\ufeff').lower()
        cleaned_cols[col] = clean_col
    df = df.rename(columns=cleaned_cols)

    # 2. Map aliases (only if canonical column is not already present)
    alias_renames = {}
    for col in df.columns:
        if col in COLUMN_ALIASES:
            canonical = COLUMN_ALIASES[col]
            if canonical not in df.columns and canonical not in alias_renames.values():
                alias_renames[col] = canonical
    if alias_renames:
        df = df.rename(columns=alias_renames)

    # 3. Handle expense & profit derivation
    if "expense" not in df.columns:
        if "revenue" in df.columns and "profit" in df.columns:
            rev_num = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
            prof_num = pd.to_numeric(df["profit"], errors="coerce").fillna(0.0)
            df["expense"] = (rev_num - prof_num).clip(lower=0.0)
        else:
            df["expense"] = 0.0

    if "profit" not in df.columns:
        if "revenue" in df.columns and "expense" in df.columns:
            rev_num = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
            exp_num = pd.to_numeric(df["expense"], errors="coerce").fillna(0.0)
            df["profit"] = rev_num - exp_num
        else:
            df["profit"] = 0.0

    # 4. Optional column defaults
    if "category" not in df.columns:
        df["category"] = "general"
    else:
        df["category"] = df["category"].fillna("general")

    if "currency" not in df.columns:
        df["currency"] = "USD"
    else:
        df["currency"] = df["currency"].fillna("USD")

    if "marketplace" not in df.columns:
        df["marketplace"] = "Direct"
    else:
        df["marketplace"] = df["marketplace"].fillna("Direct")

    if "payment_status" not in df.columns:
        df["payment_status"] = "completed"
    else:
        df["payment_status"] = df["payment_status"].fillna("completed")

    if "transaction_id" not in df.columns:
        df["transaction_id"] = ""
    else:
        df["transaction_id"] = df["transaction_id"].fillna("")

    return df


# --------------------------------------------------
# SCHEMA VALIDATION
# --------------------------------------------------

def validate_finance_schema(df: pd.DataFrame, strict: bool = False) -> List[str]:
    """
    Validates required columns in a financial dataset.
    Essential required columns: 'date' and 'revenue'.
    If strict=True, checks all 8 standard columns.
    """
    check_cols = STANDARD_COLUMNS if strict else REQUIRED_COLUMNS
    missing_columns = [
        column
        for column in check_cols
        if column not in df.columns
    ]
    return missing_columns


# --------------------------------------------------
# DATE VALIDATION
# --------------------------------------------------

def validate_dates(df):
    # Robust multi-format parsing (D5 fix)
    try:
        parsed_dates = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    except Exception:
        parsed_dates = pd.to_datetime(df["date"], errors="coerce")

    invalid_mask = parsed_dates.isna()
    invalid_rows = df[invalid_mask].copy()
    return invalid_rows


# --------------------------------------------------
# FINANCIAL VALIDATION
# --------------------------------------------------

def validate_finance_data(df):
    errors = []

    # Check for NaN / non-numeric revenue
    nan_revenue = df[df["revenue"].isna()]
    if not nan_revenue.empty:
        errors.append({
            "type": "non_numeric_or_missing_revenue",
            "count": len(nan_revenue),
            "rows": nan_revenue.index.tolist()
        })

    # Check for NaN / non-numeric expense
    nan_expense = df[df["expense"].isna()]
    if not nan_expense.empty:
        errors.append({
            "type": "non_numeric_or_missing_expense",
            "count": len(nan_expense),
            "rows": nan_expense.index.tolist()
        })

    # Check negative expense
    negative_expense = df[df["expense"] < 0]
    if not negative_expense.empty:
        errors.append({
            "type": "negative_expense",
            "count": len(negative_expense),
            "rows": negative_expense.index.tolist(),
            "values": negative_expense["expense"].tolist()
        })

    # Check negative revenue
    negative_revenue = df[df["revenue"] < 0]
    if not negative_revenue.empty:
        errors.append({
            "type": "negative_revenue",
            "count": len(negative_revenue),
            "rows": negative_revenue.index.tolist(),
            "values": negative_revenue["revenue"].tolist()
        })

    # Check cancelled / refunded payment status (D3 fix)
    if "payment_status" in df.columns:
        status_series = df["payment_status"].astype(str).str.strip().str.lower()
        excluded = status_series.isin(["refunded", "cancelled", "canceled", "failed"])
        excluded_rows = df[excluded]
        if not excluded_rows.empty:
            errors.append({
                "type": "excluded_payment_status",
                "count": len(excluded_rows),
                "rows": excluded_rows.index.tolist(),
                "values": excluded_rows["payment_status"].tolist()
            })

    return errors


# --------------------------------------------------
# REMOVE INVALID FINANCIAL ROWS
# --------------------------------------------------

def remove_invalid_finance_rows(df):
    """
    Filter out invalid financial rows:
    - Missing or non-numeric revenue/expense (D2 fix)
    - Negative revenue or expense
    - Cancelled, refunded, or failed payment statuses (D3 fix)
    """
    invalid_mask = (
        df["revenue"].isna() |
        df["expense"].isna() |
        (df["revenue"] < 0) |
        (df["expense"] < 0)
    )

    if "payment_status" in df.columns:
        status_series = df["payment_status"].astype(str).str.strip().str.lower()
        excluded_statuses = {"refunded", "cancelled", "canceled", "failed"}
        invalid_mask = invalid_mask | status_series.isin(excluded_statuses)

    invalid_rows = df[invalid_mask].copy()
    clean_df = df[~invalid_mask].copy()

    return clean_df, invalid_rows


# --------------------------------------------------
# REMOVE INVALID DATE ROWS
# --------------------------------------------------

def remove_invalid_date_rows(df):
    try:
        parsed_dates = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    except Exception:
        parsed_dates = pd.to_datetime(df["date"], errors="coerce")

    invalid_mask = parsed_dates.isna()
    invalid_rows = df[invalid_mask].copy()
    clean_df = df[~invalid_mask].copy()

    clean_df["date"] = parsed_dates[~invalid_mask].dt.strftime("%Y-%m-%d")

    return clean_df, invalid_rows


# --------------------------------------------------
# CURRENCY VALIDATION
# --------------------------------------------------

def validate_currency_data(df):
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
    from app.services.currency_service import is_supported_currency

    if "currency" not in df.columns:
        return df.iloc[0:0].copy(), df.copy()

    valid_mask = df["currency"].apply(is_supported_currency)
    invalid_rows = df[~valid_mask].copy()
    clean_df = df[valid_mask].copy()

    clean_df["currency"] = clean_df["currency"].astype(str).str.strip().str.upper()

    return clean_df, invalid_rows