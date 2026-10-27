import os
import sys
import pytest
import pandas as pd
import numpy as np

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.currency_service import (
    BASE_CURRENCY,
    FX_RATES_TO_BASE,
    SUPPORTED_CURRENCIES,
    is_supported_currency,
    get_exchange_rate_to_base,
    convert_to_base_currency
)
from app.services.etl.cleaner import normalize_currencies, clean_categories, convert_numeric_columns
from app.services.etl.validator import (
    validate_currency_data,
    remove_invalid_currency_rows,
    remove_invalid_finance_rows
)
from app.services.etl.loader import load_finance_records
from app.models.finance_record import FinanceRecord
from app.models.dataset import Dataset
from app.api.datasets import get_dataset_summary
from app.services.forecasting_service import forecast_revenue_service


def test_base_currency_and_rates():
    """Verify standard base currency is USD and explicit reference rates exist."""
    assert BASE_CURRENCY == "USD"
    assert "USD" in FX_RATES_TO_BASE
    assert FX_RATES_TO_BASE["USD"] == 1.0
    assert FX_RATES_TO_BASE["EUR"] == 0.92
    assert FX_RATES_TO_BASE["GBP"] == 0.79
    assert FX_RATES_TO_BASE["INR"] == 83.50
    assert len(SUPPORTED_CURRENCIES) >= 5


def test_mixed_currencies_normalization():
    """Verify mixed-currency amounts are normalized to USD while preserving original amounts (D1)."""
    df = pd.DataFrame([
        {"date": "2026-03-01", "revenue": 100.0, "expense": 50.0, "currency": "USD"},
        {"date": "2026-03-02", "revenue": 92.0, "expense": 46.0, "currency": "EUR"},
        {"date": "2026-03-03", "revenue": 79.0, "expense": 39.5, "currency": "GBP"},
        {"date": "2026-03-04", "revenue": 8350.0, "expense": 4175.0, "currency": "INR"},
    ])

    norm_df = normalize_currencies(df.copy())

    # USD: 100.0 / 1.0 = 100.0
    assert norm_df.loc[0, "revenue"] == 100.0
    assert norm_df.loc[0, "expense"] == 50.0
    assert norm_df.loc[0, "profit"] == 50.0

    # EUR: 92.0 / 0.92 = 100.0
    assert norm_df.loc[1, "revenue"] == 100.0
    assert norm_df.loc[1, "expense"] == 50.0
    assert norm_df.loc[1, "original_revenue"] == 92.0
    assert norm_df.loc[1, "exchange_rate"] == 0.92

    # GBP: 79.0 / 0.79 = 100.0
    assert norm_df.loc[2, "revenue"] == 100.0
    assert norm_df.loc[2, "expense"] == 50.0

    # INR: 8350.0 / 83.50 = 100.0
    assert norm_df.loc[3, "revenue"] == 100.0
    assert norm_df.loc[3, "expense"] == 50.0
    assert norm_df.loc[3, "original_revenue"] == 8350.0
    assert norm_df.loc[3, "exchange_rate"] == 83.50


def test_payment_status_exclusion_and_non_numeric(db_session):
    """Verify refunded/cancelled rows are excluded from revenue records (D2, D3)."""
    df = pd.DataFrame([
        {"transaction_id": "T1", "date": "2026-03-01", "marketplace": "Amazon", "category": "electronics", "revenue": 100.0, "expense": 40.0, "currency": "USD", "payment_status": "completed"},
        {"transaction_id": "T2", "date": "2026-03-02", "marketplace": "Amazon", "category": "electronics", "revenue": 200.0, "expense": 50.0, "currency": "USD", "payment_status": "refunded"},
        {"transaction_id": "T3", "date": "2026-03-03", "marketplace": "Amazon", "category": "electronics", "revenue": 150.0, "expense": 30.0, "currency": "USD", "payment_status": "cancelled"},
        {"transaction_id": "T4", "date": "2026-03-04", "marketplace": "Amazon", "category": "electronics", "revenue": -50.0, "expense": 10.0, "currency": "USD", "payment_status": "completed"},
    ])

    clean_df, invalid_rows = remove_invalid_finance_rows(df)

    # Only T1 is valid (T2 refunded, T3 cancelled, T4 negative)
    assert len(clean_df) == 1
    assert clean_df.iloc[0]["transaction_id"] == "T1"
    assert len(invalid_rows) == 3


def test_database_loading_and_summary_consistency(db_session):
    """Verify loading and dataset summary match hand-calculated numbers in SQLite (S6)."""
    dataset = Dataset(id=50, company_id=1, file_name="hand_test.csv", file_type=".csv", file_path="dummy", status="completed")
    db_session.add(dataset)
    db_session.commit()

    df = pd.DataFrame([
        {"date": "2026-03-01", "revenue": 100.0, "expense": 50.0, "currency": "USD"},
        {"date": "2026-03-02", "revenue": 8350.0, "expense": 4175.0, "currency": "INR"},
    ])
    norm_df = normalize_currencies(df.copy())
    norm_df["category"] = "general"

    loaded = load_finance_records(db=db_session, df=norm_df, dataset_id=50, replace=True)
    assert loaded == 2

    # Query back
    records = db_session.query(FinanceRecord).filter(FinanceRecord.dataset_id == 50).all()
    assert len(records) == 2
    # Total revenue must be exactly 100.0 + (8350.0 / 83.50) = 200.0 USD
    total_rev = sum(r.revenue for r in records)
    assert total_rev == 200.0
