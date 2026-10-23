"""
NexusAI Idempotent Dataset Reprocessing Service
Reprocesses uploaded datasets to apply currency normalization and schema validation
without overwriting raw files or duplicating records.
"""

import os
from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.dataset import Dataset
from app.models.metadata import Metadata
from app.services.etl.reader import read_csv, read_excel
from app.services.etl.cleaner import (
    clean_categories,
    remove_duplicates,
    convert_numeric_columns,
    handle_missing_values,
    normalize_currencies
)
from app.services.etl.validator import (
    validate_finance_schema,
    remove_invalid_finance_rows,
    remove_invalid_date_rows,
    remove_invalid_currency_rows
)
from app.services.etl.loader import load_finance_records
from app.services.etl.metadata import calculate_metadata
from app.services.currency_service import BASE_CURRENCY, FX_RATES_TO_BASE


def reprocess_dataset_service(dataset_id: int) -> Dict[str, Any]:
    """
    Safely and idempotently reprocess an existing dataset from its preserved source file.
    Normalizes multi-currency records to USD base currency while preserving original
    amounts and transaction currencies in the database.
    """
    db: Session = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset #{dataset_id} does not exist."
            )

        if not dataset.file_path or not os.path.exists(dataset.file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Original source file for dataset #{dataset_id} is missing from storage."
            )

        # 1. Read source file (Read-only, preserves source file on disk)
        file_ext = os.path.splitext(dataset.file_path)[1].lower()
        if file_ext == ".csv":
            df = read_csv(dataset.file_path)
        elif file_ext in [".xlsx", ".xls"]:
            df = read_excel(dataset.file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_ext}"
            )

        original_rows = len(df)

        # 2. Validate schema
        missing_cols = validate_finance_schema(df)
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source file is missing required columns: {missing_cols}"
            )

        # 3. Clean Categories & Duplicates
        df = clean_categories(df)
        df, duplicates_removed = remove_duplicates(df)
        df = convert_numeric_columns(df)
        df = handle_missing_values(df)

        # 4. Validate Financial Data (non-negative revenue/expense)
        clean_df, invalid_finance = remove_invalid_finance_rows(df)

        # 5. Validate Dates
        clean_df, invalid_dates = remove_invalid_date_rows(clean_df)

        # 6. Validate Currencies
        clean_df, invalid_currencies = remove_invalid_currency_rows(clean_df)

        total_invalid_rows = len(invalid_finance) + len(invalid_dates) + len(invalid_currencies)

        # 7. Multi-Currency Normalization to Base Currency (USD)
        clean_df = normalize_currencies(clean_df)

        # Track detected currencies
        detected_currencies = sorted(clean_df["currency"].unique().tolist())

        # 8. Idempotently Reload Records (replace=True prevents duplicates)
        records_loaded = load_finance_records(
            db=db,
            df=clean_df,
            dataset_id=dataset.id,
            replace=True
        )

        # 9. Recalculate Metadata
        metadata_vals = calculate_metadata(
            original_rows=original_rows,
            cleaned_rows=len(clean_df),
            duplicates_removed=duplicates_removed,
            invalid_rows=total_invalid_rows
        )

        metadata_obj = db.query(Metadata).filter(Metadata.dataset_id == dataset.id).first()
        if metadata_obj:
            metadata_obj.total_rows = metadata_vals["total_rows"]
            metadata_obj.cleaned_rows = metadata_vals["cleaned_rows"]
            metadata_obj.duplicates_removed = metadata_vals["duplicates_removed"]
            metadata_obj.invalid_rows = metadata_vals["invalid_rows"]
            metadata_obj.data_quality_score = metadata_vals["data_quality_score"]
            metadata_obj.status = metadata_vals["status"]
        else:
            metadata_obj = Metadata(
                dataset_id=dataset.id,
                total_rows=metadata_vals["total_rows"],
                cleaned_rows=metadata_vals["cleaned_rows"],
                duplicates_removed=metadata_vals["duplicates_removed"],
                invalid_rows=metadata_vals["invalid_rows"],
                data_quality_score=metadata_vals["data_quality_score"],
                status=metadata_vals["status"]
            )
            db.add(metadata_obj)

        db.commit()

        # 10. Compute Summary Metrics in Base Currency
        norm_rev = round(float(clean_df["revenue"].sum()), 2)
        norm_exp = round(float(clean_df["expense"].sum()), 2)
        norm_prof = round(float(clean_df["profit"].sum()), 2)

        return {
            "dataset_id": dataset.id,
            "file_name": dataset.file_name,
            "status": "reprocessed_successfully",
            "base_currency": BASE_CURRENCY,
            "records_loaded": records_loaded,
            "detected_currencies": detected_currencies,
            "duplicates_removed": duplicates_removed,
            "invalid_rows_breakdown": {
                "invalid_financial": len(invalid_finance),
                "invalid_dates": len(invalid_dates),
                "invalid_currencies": len(invalid_currencies),
                "total_invalid": total_invalid_rows
            },
            "normalized_totals": {
                "total_revenue_usd": norm_rev,
                "total_expenses_usd": norm_exp,
                "total_profit_usd": norm_prof
            }
        }
    finally:
        db.close()
