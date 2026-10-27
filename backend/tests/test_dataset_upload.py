import io
import os
import pytest
import pandas as pd
from starlette.testclient import TestClient

from app.main import app
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord
from app.models.metadata import Metadata
from app.services.etl.validator import (
    standardize_finance_dataframe,
    validate_finance_schema,
    COLUMN_ALIASES
)
from app.services.etl.cleaner import convert_numeric_columns
from app.services.etl.reprocessor import reprocess_dataset_service


def test_standardize_finance_dataframe_aliases():
    """Verify alias mapping (expenses -> expense, sales -> revenue) and column normalization."""
    raw_df = pd.DataFrame({
        " Date ": ["2026-09-01", "2026-09-02"],
        "Sales": [1200.0, 1500.0],
        "Expenses": [700.0, 900.0],
        "Category": ["Electronics", "Electronics"]
    })

    clean_df = standardize_finance_dataframe(raw_df)

    assert "date" in clean_df.columns
    assert "revenue" in clean_df.columns
    assert "expense" in clean_df.columns
    assert "category" in clean_df.columns
    assert "currency" in clean_df.columns
    assert clean_df["currency"].iloc[0] == "USD"
    assert clean_df.loc[0, "revenue"] == 1200.0
    assert clean_df.loc[0, "expense"] == 700.0
    assert clean_df.loc[0, "profit"] == 500.0


def test_standardize_finance_dataframe_currency_stripping():
    """Verify formatted currency strings with $, commas, and spaces are parsed correctly."""
    raw_df = pd.DataFrame({
        "date": ["2026-09-01"],
        "revenue": ["$1,250.50"],
        "expense": ["$750.25"],
    })

    std_df = standardize_finance_dataframe(raw_df)
    clean_df = convert_numeric_columns(std_df)

    assert clean_df.loc[0, "revenue"] == 1250.50
    assert clean_df.loc[0, "expense"] == 750.25
    assert clean_df.loc[0, "category"] == "general"


def test_validation_dataset_upload_endpoint(db_session, auth_headers):
    """
    Verify uploading a dataset with columns 'date,category,revenue,expenses,profit'
    (matching nexusai_validation_dataset.csv) succeeds with 200 OK and status 'completed'.
    """
    client = TestClient(app)

    csv_content = (
        "date,category,revenue,expenses,profit\n"
        "2026-09-01,Electronics,1200.0,700.0,500.0\n"
        "2026-09-02,Books,300.0,180.0,120.0\n"
        "2026-09-03,Home & Kitchen,800.0,500.0,300.0\n"
    ).encode("utf-8")

    file_tuple = ("nexus_test_dataset.csv", io.BytesIO(csv_content), "text/csv")

    response = client.post(
        "/upload",
        files={"file": file_tuple},
        headers=auth_headers
    )

    assert response.status_code == 200, f"Upload failed with {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "completed"
    assert data["records_loaded"] == 3
    assert data["invalid_rows"] == 0
    assert data["data_quality_score"] == 100.0

    # Verify records stored in database
    ds_id = data["dataset_id"]
    records = db_session.query(FinanceRecord).filter(FinanceRecord.dataset_id == ds_id).all()
    assert len(records) == 3
    total_rev = sum(r.revenue for r in records)
    assert total_rev == 2300.0


def test_upload_missing_mandatory_columns_returns_400(auth_headers):
    """Verify that uploading a dataset missing both date and revenue returns 400 Bad Request."""
    client = TestClient(app)

    invalid_csv = (
        "user_id,item_name,quantity\n"
        "101,Keyboard,2\n"
        "102,Mouse,5\n"
    ).encode("utf-8")

    file_tuple = ("invalid_schema.csv", io.BytesIO(invalid_csv), "text/csv")

    response = client.post(
        "/upload",
        files={"file": file_tuple},
        headers=auth_headers
    )

    assert response.status_code == 400
    err_json = response.json()
    assert "detail" in err_json
    detail = err_json["detail"]
    assert "missing_columns" in detail
    assert "date" in detail["missing_columns"]
    assert "revenue" in detail["missing_columns"]


def test_reprocess_failed_dataset_service(db_session):
    """
    Verify reprocess_dataset_service correctly fixes a previously failed dataset
    using the updated standardization pipeline.
    """
    # Create test source CSV file on disk
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_csv_path = os.path.join(backend_dir, "uploads", "test_reprocess_sample.csv")
    os.makedirs(os.path.dirname(test_csv_path), exist_ok=True)

    with open(test_csv_path, "w", encoding="utf-8") as f:
        f.write("date,category,revenue,expenses,profit\n")
        f.write("2026-09-01,Electronics,1200.0,700.0,500.0\n")
        f.write("2026-09-02,Clothing,800.0,400.0,400.0\n")

    try:
        # Create dataset in DB marked as failed
        dataset = Dataset(
            company_id=1,
            file_name="test_reprocess_sample.csv",
            file_type=".csv",
            file_path=test_csv_path,
            status="failed"
        )
        db_session.add(dataset)
        db_session.commit()
        db_session.refresh(dataset)

        result = reprocess_dataset_service(dataset.id)

        assert result["status"] == "reprocessed_successfully"
        assert result["records_loaded"] == 2
        assert result["normalized_totals"]["total_revenue_usd"] == 2000.0

        # Dataset status in DB should now be 'completed'
        db_session.refresh(dataset)
        assert dataset.status == "completed"

    finally:
        if os.path.exists(test_csv_path):
            try:
                os.remove(test_csv_path)
            except Exception:
                pass
