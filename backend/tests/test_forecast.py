import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure OpenBLAS thread constraint on Windows
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

# Add backend directory to path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.services.forecasting_service import forecast_revenue_service
from fastapi import HTTPException


class TestRevenueForecastingAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_valid_forecast_7_days(self):
        """Test valid forecasting request for 7-day horizon on dataset 1"""
        response = self.client.post(
            "/ai/forecast/revenue",
            json={"dataset_id": 1, "horizon_days": 7}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["dataset_id"], 1)
        self.assertEqual(data["horizon_days"], 7)
        self.assertEqual(len(data["forecast_data"]), 7)
        self.assertGreater(len(data["historical_data"]), 0)

        # Check summary structure
        summary = data["summary"]
        self.assertIn("total_projected_revenue", summary)
        self.assertIn("average_daily_projected_revenue", summary)
        self.assertIn("total_historical_revenue", summary)
        self.assertIn("historical_days_count", summary)

        # Check metadata & evaluation
        meta = data["model_metadata"]
        self.assertIn("held_out_evaluation", meta)
        self.assertIn("assumptions", meta)
        self.assertIn("limitations", meta)

    def test_valid_forecast_30_days(self):
        """Test valid forecasting request for 30-day horizon on dataset 1"""
        response = self.client.post(
            "/ai/forecast/revenue",
            json={"dataset_id": 1, "horizon_days": 30}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["horizon_days"], 30)
        self.assertEqual(len(data["forecast_data"]), 30)

    def test_valid_forecast_90_days(self):
        """Test valid forecasting request for 90-day horizon on dataset 1"""
        response = self.client.post(
            "/ai/forecast/revenue",
            json={"dataset_id": 1, "horizon_days": 90}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["horizon_days"], 90)
        self.assertEqual(len(data["forecast_data"]), 90)

    def test_non_existent_dataset_id_returns_404(self):
        """Test that requesting a non-existent dataset ID returns HTTP 404"""
        response = self.client.post(
            "/ai/forecast/revenue",
            json={"dataset_id": 99999, "horizon_days": 30}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("does not exist", response.json()["detail"])

    def test_invalid_horizon_returns_422(self):
        """Test that an unsupported horizon (e.g. 15 days) returns HTTP 422"""
        response = self.client.post(
            "/ai/forecast/revenue",
            json={"dataset_id": 1, "horizon_days": 15}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("Supported horizons are 7, 30, or 90", response.json()["detail"])

    def test_malformed_negative_dataset_id_returns_422(self):
        """Test that a negative or zero dataset_id returns HTTP 422 validation error"""
        response = self.client.post(
            "/ai/forecast/revenue",
            json={"dataset_id": -5, "horizon_days": 30}
        )
        self.assertEqual(response.status_code, 422)

    def test_insufficient_historical_data_raises_http_400(self):
        """Test that datasets with fewer than 5 distinct days raise a descriptive 400 error"""
        # Mock SessionLocal and DB query to return only 2 records
        mock_dataset = MagicMock()
        mock_dataset.id = 99
        mock_dataset.file_name = "sparse_data.csv"
        mock_dataset.file_path = None

        mock_r1 = MagicMock(revenue=100.0, date="2026-01-01")
        mock_r2 = MagicMock(revenue=150.0, date="2026-01-02")

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        # First call for Dataset, second for FinanceRecord
        mock_query.filter.return_value.first.return_value = mock_dataset
        mock_query.filter.return_value.all.return_value = [mock_r1, mock_r2]

        with patch("app.services.forecasting_service.SessionLocal", return_value=mock_db):
            with self.assertRaises(HTTPException) as ctx:
                forecast_revenue_service(dataset_id=99, horizon_days=7)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("Insufficient historical observations", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
