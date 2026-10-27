import os
import re
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.company import Company
from app.models.dataset import Dataset
from app.models.metadata import Metadata

from app.services.etl.reader import read_csv, read_excel

from app.services.etl.cleaner import (
    clean_categories,
    remove_duplicates,
    convert_numeric_columns,
    handle_missing_values,
    calculate_profit,
    normalize_currencies
)

from app.services.etl.validator import (
    validate_finance_schema,
    standardize_finance_dataframe,
    validate_dates,
    validate_finance_data,
    remove_invalid_finance_rows,
    remove_invalid_date_rows,
    remove_invalid_currency_rows
)

from app.services.etl.loader import load_finance_records
from app.services.etl.metadata import calculate_metadata

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB limit


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # --------------------------------------------------
    # 1. Check file type
    # --------------------------------------------------

    allowed_extensions = [".csv", ".xlsx", ".xls"]
    raw_filename = file.filename or "data.csv"
    file_extension = os.path.splitext(raw_filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are allowed."
        )

    # --------------------------------------------------
    # 2. Check file size & Save with sanitized unique path (S5 fix)
    # --------------------------------------------------

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds maximum allowed limit of 20MB."
        )

    # Sanitize original basename to prevent path traversal
    safe_basename = re.sub(r'[^a-zA-Z0-9_.-]', '_', os.path.basename(raw_filename))
    unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_basename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # --------------------------------------------------
    # 3. Connect to database
    # --------------------------------------------------

    db: Session = SessionLocal()
    dataset = None

    try:

        # --------------------------------------------------
        # 4. Create Dataset record
        # --------------------------------------------------

        dataset = Dataset(
            company_id=1,
            file_name=safe_basename,
            file_type=file_extension,
            file_path=file_path,
            status="processing"
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        # --------------------------------------------------
        # 5. Read CSV / Excel
        # --------------------------------------------------

        if file_extension == ".csv":
            df = read_csv(file_path)
        else:
            df = read_excel(file_path)

        if df.empty:
            dataset.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="The uploaded file contains no data rows."
            )

        # Standardize headers, map synonyms/aliases, and populate safe defaults
        df = standardize_finance_dataframe(df)
        original_rows = len(df)

        # --------------------------------------------------
        # 6. Schema validation
        # --------------------------------------------------

        missing_columns = validate_finance_schema(df)

        if missing_columns:
            dataset.status = "failed"
            db.commit()

            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Required columns are missing: {', '.join(missing_columns)}. Financial datasets must include date and revenue (or sales).",
                    "missing_columns": missing_columns,
                    "detected_columns": list(df.columns)
                }
            )

        # --------------------------------------------------
        # 7. Clean data
        # --------------------------------------------------

        df = clean_categories(df)
        df, duplicates_removed = remove_duplicates(df)
        df = convert_numeric_columns(df)
        df = handle_missing_values(df)

        # --------------------------------------------------
        # 8. Financial validation
        # --------------------------------------------------

        validation_errors = validate_finance_data(df)
        clean_df, invalid_finance_rows = remove_invalid_finance_rows(df)

        # --------------------------------------------------
        # 9. Date validation
        # --------------------------------------------------

        invalid_date_rows = validate_dates(clean_df)
        clean_df, invalid_date_rows = remove_invalid_date_rows(clean_df)

        # --------------------------------------------------
        # 10. Currency validation
        # --------------------------------------------------
        clean_df, invalid_currency_rows = remove_invalid_currency_rows(clean_df)

        # --------------------------------------------------
        # 11. Total invalid rows
        # --------------------------------------------------

        total_invalid_rows = (
            len(invalid_finance_rows)
            + len(invalid_date_rows)
            + len(invalid_currency_rows)
        )

        # --------------------------------------------------
        # 12. Currency normalization to Base Currency (USD)
        # --------------------------------------------------

        clean_df = normalize_currencies(clean_df)

        # --------------------------------------------------
        # 13. Load clean records
        # --------------------------------------------------

        records_loaded = load_finance_records(
            db=db,
            df=clean_df,
            dataset_id=dataset.id
        )

        # --------------------------------------------------
        # 14. Calculate & Save metadata
        # --------------------------------------------------

        metadata_data = calculate_metadata(
            original_rows=original_rows,
            cleaned_rows=len(clean_df),
            duplicates_removed=duplicates_removed,
            invalid_rows=total_invalid_rows
        )

        metadata = Metadata(
            dataset_id=dataset.id,
            total_rows=metadata_data["total_rows"],
            cleaned_rows=metadata_data["cleaned_rows"],
            duplicates_removed=metadata_data["duplicates_removed"],
            invalid_rows=metadata_data["invalid_rows"],
            data_quality_score=metadata_data["data_quality_score"],
            status=metadata_data["status"]
        )

        db.add(metadata)
        db.commit()
        db.refresh(metadata)

        # --------------------------------------------------
        # 15. Update dataset status
        # --------------------------------------------------

        dataset.status = "completed"
        db.commit()

        # --------------------------------------------------
        # 16. Return API response (safe from path leakage)
        # --------------------------------------------------

        return {
            "status": "completed",
            "dataset_id": dataset.id,
            "filename": dataset.file_name,
            "file_type": dataset.file_type,
            "records_loaded": records_loaded,
            "duplicates_removed": duplicates_removed,
            "invalid_financial_rows": len(invalid_finance_rows),
            "invalid_date_rows": len(invalid_date_rows),
            "invalid_currency_rows": len(invalid_currency_rows),
            "invalid_rows": total_invalid_rows,
            "clean_rows": len(clean_df),
            "data_quality_score": metadata.data_quality_score
        }

    except HTTPException:
        if dataset and dataset.id:
            try:
                dataset.status = "failed"
                db.commit()
            except Exception:
                db.rollback()
        raise

    except Exception as e:
        logger.exception("Upload processing error: %s", str(e))
        db.rollback()
        if dataset and dataset.id:
            try:
                dataset.status = "failed"
                db.commit()
            except Exception:
                db.rollback()

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the uploaded file."
        )

    finally:
        db.close()