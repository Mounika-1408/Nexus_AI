import os
import sys
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord
from app.services.forecasting_service import forecast_revenue_service, optimize_holt_parameters


@pytest.fixture
def client():
    return TestClient(app)


def test_unauthenticated_request_returns_401(client, seeded_dataset):
    """Verify endpoint is guarded by authentication (S2 fix)."""
    response = client.post(
        "/ai/forecast/revenue",
        json={"dataset_id": seeded_dataset.id, "horizon_days": 30}
    )
    assert response.status_code == 401


def test_valid_forecast_with_auth(client, seeded_dataset, auth_headers):
    """Verify authenticated forecast works correctly against seeded dataset."""
    response = client.post(
        "/ai/forecast/revenue",
        json={"dataset_id": seeded_dataset.id, "horizon_days": 30},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == seeded_dataset.id
    assert data["horizon_days"] == 30
    assert len(data["forecast_data"]) == 30
    assert data["summary"]["total_projected_revenue"] > 0
    assert "held_out_evaluation" in data["model_metadata"]
    assert "warnings" in data


def test_trailing_zero_collapse_prevention(db_session):
    """
    Verify F1 fix: 90 healthy days of $100 followed by 10 zero days does NOT collapse to $0
    or yield -100.0% change.
    """
    # Create dataset 200 with 90 active days + 10 zero days
    ds = Dataset(id=200, company_id=1, file_name="zero_tail.csv", file_type=".csv", file_path="dummy", status="completed")
    db_session.add(ds)
    db_session.commit()

    records = []
    base_date = pd.to_datetime("2025-10-01")
    for i in range(90):
        records.append(FinanceRecord(
            dataset_id=200,
            date=(base_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
            revenue=100.0,
            expenses=50.0,
            profit=50.0,
            currency="USD",
            original_revenue=100.0,
            original_expenses=50.0,
            exchange_rate=1.0
        ))
    for i in range(10):
        records.append(FinanceRecord(
            dataset_id=200,
            date=(base_date + pd.Timedelta(days=90 + i)).strftime("%Y-%m-%d"),
            revenue=0.0,
            expenses=0.0,
            profit=0.0,
            currency="USD",
            original_revenue=0.0,
            original_expenses=0.0,
            exchange_rate=1.0
        ))

    db_session.add_all(records)
    db_session.commit()

    res = forecast_revenue_service(dataset_id=200, horizon_days=30)
    summary = res["summary"]

    # F1 fix verification: total projected revenue must be > 0 and change must not be -100%
    assert summary["total_projected_revenue"] > 0.0
    assert summary["projected_change_percent"] != -100.0
    # Must have warning about trailing zeros
    assert len(res["warnings"]) > 0
    assert any("trailing zero" in w.lower() for w in res["warnings"])


def test_parameter_optimization_stability():
    """Verify dynamic parameter optimization selects stable smoothing parameters (F2 fix)."""
    y = np.array([50, 52, 55, 60, 58, 62, 65, 70, 68, 72.0])
    alpha, beta, phi = optimize_holt_parameters(y)
    assert 0.05 <= alpha <= 0.50
    assert 0.01 <= beta <= 0.20
    assert 0.80 <= phi <= 0.98


@pytest.mark.parametrize("horizon", [7, 30, 90])
def test_forecast_horizons_produce_correct_future_calendar_days(client, seeded_dataset, auth_headers, horizon):
    """
    Verify 7, 30, and 90 day horizons produce the exact count of future calendar days,
    consistent summary dates, and do not accidentally display past dates (Requirements 4, 5, 6, 8).
    """
    from datetime import datetime
    today = datetime.now().date()

    response = client.post(
        "/ai/forecast/revenue",
        json={"dataset_id": seeded_dataset.id, "horizon_days": horizon},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]
    fc_points = data["forecast_data"]

    # 1. Horizon count checks
    assert data["horizon_days"] == horizon
    assert summary["forecast_days_count"] == horizon
    assert len(fc_points) == horizon

    # 2. Consistency across summary, points, and labels
    assert summary["forecast_start_date"] == fc_points[0]["date"]
    assert summary["forecast_end_date"] == fc_points[-1]["date"]

    # 3. Ensure no past dates are displayed: all forecast dates must be in the future relative to today
    for pt in fc_points:
        pt_date = pd.to_datetime(pt["date"]).date()
        assert pt_date >= today, f"Forecast date {pt['date']} should not be in the past relative to {today}"

    # 4. Strictly consecutive daily progression
    expected_dates = pd.date_range(start=summary["forecast_start_date"], periods=horizon, freq="D").strftime("%Y-%m-%d").tolist()
    actual_dates = [pt["date"] for pt in fc_points]
    assert actual_dates == expected_dates

    # 5. Keep historical actual dates strictly separate from forecast dates
    hist_dates = {pt["date"] for pt in data["historical_data"]}
    fc_dates_set = set(actual_dates)
    assert hist_dates.isdisjoint(fc_dates_set), "Historical actual dates must not overlap with forecast dates"


@pytest.mark.parametrize("horizon,expected_start,expected_end", [
    (7, "2026-10-25", "2026-10-31"),
    (30, "2026-10-25", "2026-11-23"),
    (90, "2026-10-25", "2027-01-22"),
])
def test_forecast_with_explicit_anchor_date(client, seeded_dataset, auth_headers, horizon, expected_start, expected_end):
    """Verify forecast accurately anchors to explicit anchor date for 7, 30, and 90 day horizons."""
    response = client.post(
        "/ai/forecast/revenue",
        json={
            "dataset_id": seeded_dataset.id,
            "horizon_days": horizon,
            "anchor_date": "2026-10-24"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]

    assert summary["forecast_start_date"] == expected_start
    assert summary["forecast_end_date"] == expected_end
    assert len(data["forecast_data"]) == horizon
    assert data["forecast_data"][0]["date"] == expected_start
    assert data["forecast_data"][-1]["date"] == expected_end


def test_future_dataset_anchors_after_latest_record(db_session):
    """
    Verify that if a dataset already has records extending into the future beyond today,
    the forecast anchors after the dataset's latest record to preserve separation (Requirement 5, 7).
    """
    ds = Dataset(id=300, company_id=1, file_name="future_records.csv", file_type=".csv", file_path="dummy", status="completed")
    db_session.add(ds)
    db_session.commit()

    records = []
    base_date = pd.to_datetime("2028-06-01")
    for i in range(15):
        records.append(FinanceRecord(
            dataset_id=300,
            date=(base_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
            revenue=150.0,
            expenses=60.0,
            profit=90.0,
            currency="USD",
            original_revenue=150.0,
            original_expenses=60.0,
            exchange_rate=1.0
        ))
    db_session.add_all(records)
    db_session.commit()

    res = forecast_revenue_service(dataset_id=300, horizon_days=7)
    summary = res["summary"]

    # Since dataset ends on 2028-06-15, forecast should anchor to 2028-06-15 and start on 2028-06-16
    assert summary["historical_end_date"] == "2028-06-15"
    assert summary["forecast_start_date"] == "2028-06-16"
    assert summary["forecast_end_date"] == "2028-06-22"
    assert len(res["forecast_data"]) == 7

    hist_dates = {pt["date"] for pt in res["historical_data"]}
    fc_dates = {pt["date"] for pt in res["forecast_data"]}
    assert hist_dates.isdisjoint(fc_dates)

