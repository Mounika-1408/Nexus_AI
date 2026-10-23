import os
import sys
import unittest
import pandas as pd
import numpy as np

# Ensure OpenBLAS thread constraint on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

# Add backend directory to path
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
from app.services.etl.cleaner import normalize_currencies
from app.services.etl.validator import (
    validate_currency_data,
    remove_invalid_currency_rows
)
from app.services.etl.loader import load_finance_records
from app.services.etl.reprocessor import reprocess_dataset_service
from app.services.forecasting_service import forecast_revenue_service
from app.api.datasets import get_dataset_summary
from app.database.connection import SessionLocal
from app.models.finance_record import FinanceRecord


class TestCurrencyNormalization(unittest.TestCase):

    def test_base_currency_and_rates_definition(self):
        """Verify standard base currency is USD and explicit reference rates exist."""
        self.assertEqual(BASE_CURRENCY, "USD")
        self.assertIn("USD", FX_RATES_TO_BASE)
        self.assertEqual(FX_RATES_TO_BASE["USD"], 1.0)
        self.assertEqual(FX_RATES_TO_BASE["EUR"], 0.92)
        self.assertEqual(FX_RATES_TO_BASE["GBP"], 0.79)
        self.assertEqual(FX_RATES_TO_BASE["INR"], 83.50)
        self.assertGreater(len(SUPPORTED_CURRENCIES), 4)

    def test_mixed_currencies_normalization(self):
        """Verify mixed-currency amounts are normalized to USD while preserving original amounts."""
        df = pd.DataFrame([
            {"date": "2026-03-01", "revenue": 100.0, "expense": 50.0, "currency": "USD"},
            {"date": "2026-03-02", "revenue": 92.0, "expense": 46.0, "currency": "EUR"},
            {"date": "2026-03-03", "revenue": 79.0, "expense": 39.5, "currency": "GBP"},
            {"date": "2026-03-04", "revenue": 8350.0, "expense": 4175.0, "currency": "INR"},
        ])

        norm_df = normalize_currencies(df.copy())

        # USD: 100.0 / 1.0 = 100.0
        self.assertEqual(norm_df.loc[0, "revenue"], 100.0)
        self.assertEqual(norm_df.loc[0, "original_revenue"], 100.0)
        self.assertEqual(norm_df.loc[0, "exchange_rate"], 1.0)

        # EUR: 92.0 / 0.92 = 100.0
        self.assertEqual(norm_df.loc[1, "revenue"], 100.0)
        self.assertEqual(norm_df.loc[1, "original_revenue"], 92.0)
        self.assertEqual(norm_df.loc[1, "exchange_rate"], 0.92)

        # GBP: 79.0 / 0.79 = 100.0
        self.assertEqual(norm_df.loc[2, "revenue"], 100.0)
        self.assertEqual(norm_df.loc[2, "original_revenue"], 79.0)
        self.assertEqual(norm_df.loc[2, "exchange_rate"], 0.79)

        # INR: 8350.0 / 83.50 = 100.0
        self.assertEqual(norm_df.loc[3, "revenue"], 100.0)
        self.assertEqual(norm_df.loc[3, "original_revenue"], 8350.0)
        self.assertEqual(norm_df.loc[3, "exchange_rate"], 83.50)

        # Check profit in normalized base
        for idx in range(4):
            self.assertEqual(norm_df.loc[idx, "profit"], 50.0)

    def test_usd_only_data_preserves_values_identically(self):
        """Verify USD-only data has rate 1.0 and identical normalized and original values."""
        df = pd.DataFrame([
            {"date": "2026-03-01", "revenue": 250.75, "expense": 120.25, "currency": "USD"},
            {"date": "2026-03-02", "revenue": 180.50, "expense": 90.00, "currency": "usd"},
        ])

        norm_df = normalize_currencies(df.copy())
        self.assertEqual(norm_df.loc[0, "revenue"], 250.75)
        self.assertEqual(norm_df.loc[0, "original_revenue"], 250.75)
        self.assertEqual(norm_df.loc[0, "exchange_rate"], 1.0)
        self.assertEqual(norm_df.loc[1, "revenue"], 180.50)
        self.assertEqual(norm_df.loc[1, "currency"], "USD")

    def test_unsupported_and_missing_currency_validation(self):
        """Verify unknown or missing currencies are excluded and not silently treated as USD."""
        df = pd.DataFrame([
            {"date": "2026-03-01", "revenue": 100.0, "expense": 20.0, "currency": "USD"},
            {"date": "2026-03-02", "revenue": 500.0, "expense": 50.0, "currency": "XYZ"},  # Unsupported
            {"date": "2026-03-03", "revenue": 300.0, "expense": 30.0, "currency": None},   # Missing
            {"date": "2026-03-04", "revenue": 200.0, "expense": 20.0, "currency": ""},     # Empty
            {"date": "2026-03-05", "revenue": 150.0, "expense": 15.0, "currency": "EUR"},  # Valid
        ])

        errors = validate_currency_data(df)
        self.assertGreater(len(errors), 0)
        self.assertEqual(errors[0]["count"], 3)  # XYZ, None, ""

        clean_df, invalid_rows = remove_invalid_currency_rows(df)
        self.assertEqual(len(clean_df), 2)  # Only USD and EUR remain
        self.assertEqual(len(invalid_rows), 3)

        # Make sure invalid rows were NOT coerced to USD
        self.assertIn("XYZ", invalid_rows["currency"].values)

    def test_idempotent_reprocessing_dataset_1(self):
        """Verify reprocessing dataset 1 is idempotent and does not produce duplicate records."""
        # Run reprocessing twice
        res1 = reprocess_dataset_service(1)
        self.assertEqual(res1["status"], "reprocessed_successfully")
        self.assertEqual(res1["records_loaded"], 8)

        res2 = reprocess_dataset_service(1)
        self.assertEqual(res2["status"], "reprocessed_successfully")
        self.assertEqual(res2["records_loaded"], 8)

        # Verify DB row count is exactly 8
        db = SessionLocal()
        try:
            records = db.query(FinanceRecord).filter(FinanceRecord.dataset_id == 1).all()
            self.assertEqual(len(records), 8)

            # Confirm March 5 record has INR original currency and normalized revenue ~41.90 USD
            m5_rec = [r for r in records if str(r.date).strip() == "2026-03-05"]
            self.assertEqual(len(m5_rec), 1)
            self.assertEqual(m5_rec[0].currency, "INR")
            self.assertEqual(m5_rec[0].original_revenue, 3499.00)
            self.assertEqual(m5_rec[0].exchange_rate, 83.50)
            self.assertEqual(m5_rec[0].revenue, 41.90)
        finally:
            db.close()

    def test_consistency_records_summary_and_forecast(self):
        """Verify revenue total consistency between finance_records, dataset summary, and forecast."""
        db = SessionLocal()
        try:
            records = db.query(FinanceRecord).filter(FinanceRecord.dataset_id == 1).all()
            total_records_rev = round(sum(r.revenue or 0 for r in records), 2)
        finally:
            db.close()

        summary = get_dataset_summary(1)
        total_summary_rev = summary["total_revenue"]

        forecast = forecast_revenue_service(dataset_id=1, horizon_days=30)
        total_forecast_hist_rev = forecast["summary"]["total_historical_revenue"]

        # All three must match exactly
        self.assertEqual(total_records_rev, total_summary_rev)
        self.assertEqual(total_summary_rev, total_forecast_hist_rev)
        self.assertEqual(total_records_rev, 594.13)


if __name__ == "__main__":
    unittest.main()
