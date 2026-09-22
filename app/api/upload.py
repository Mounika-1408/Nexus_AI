import os

from fastapi import APIRouter, UploadFile, File, HTTPException
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
    calculate_profit
)

from app.services.etl.validator import (
    validate_finance_schema,
    validate_dates,
    validate_finance_data,
    remove_invalid_finance_rows,
    remove_invalid_date_rows
)

from app.services.etl.loader import load_finance_records
from app.services.etl.metadata import calculate_metadata


router = APIRouter()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # --------------------------------------------------
    # 1. Check file type
    # --------------------------------------------------

    allowed_extensions = [".csv", ".xlsx", ".xls"]

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are allowed."
        )

    # --------------------------------------------------
    # 2. Save uploaded file
    # --------------------------------------------------

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # --------------------------------------------------
    # 3. Connect to database
    # --------------------------------------------------

    db: Session = SessionLocal()

    try:

        # --------------------------------------------------
        # 4. Create Dataset record
        # --------------------------------------------------

        dataset = Dataset(
            company_id=1,
            file_name=file.filename,
            file_type=file_extension,
            file_path=file_path,
            status="processing"
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        print("\nDataset created:")
        print("Dataset ID:", dataset.id)

        # --------------------------------------------------
        # 5. Read CSV / Excel
        # --------------------------------------------------

        if file_extension in [".csv", ".xlsx", ".xls"]:

            if file_extension == ".csv":
                df = read_csv(file_path)
            else:
                df = read_excel(file_path)

            original_rows = len(df)

            print("\nUploaded dataset:")
            print("Rows:", original_rows)
            print("Columns:", df.columns.tolist())

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
                        "message": "Required columns are missing.",
                        "missing_columns": missing_columns
                    }
                )

            print("\nSchema validation:")
            print("Status: passed")

            # --------------------------------------------------
            # 7. Clean data
            # --------------------------------------------------

            df = clean_categories(df)

            df, duplicates_removed = remove_duplicates(df)

            df = convert_numeric_columns(df)

            df = handle_missing_values(df)

            print("\nAfter cleaning:")
            print("Rows:", len(df))
            print("Duplicates removed:", duplicates_removed)

            # --------------------------------------------------
            # 8. Financial validation
            # --------------------------------------------------

            validation_errors = validate_finance_data(df)

            clean_df, invalid_finance_rows = remove_invalid_finance_rows(df)

            print("\nFinancial validation:")
            print("Errors:", validation_errors)
            print(
                "Invalid financial rows:",
                len(invalid_finance_rows)
            )

            # --------------------------------------------------
            # 9. Date validation
            # --------------------------------------------------

            invalid_date_rows = validate_dates(clean_df)

            print("\nDate validation:")
            print(
                "Invalid date rows:",
                len(invalid_date_rows)
            )

            # Remove invalid dates
            clean_df, invalid_date_rows = remove_invalid_date_rows(
                clean_df
            )

            # --------------------------------------------------
            # 10. Total invalid rows
            # --------------------------------------------------

            total_invalid_rows = (
                len(invalid_finance_rows)
                + len(invalid_date_rows)
            )

            print("\nValidation summary:")
            print(
                "Invalid financial rows:",
                len(invalid_finance_rows)
            )
            print(
                "Invalid date rows:",
                len(invalid_date_rows)
            )
            print(
                "Total invalid rows:",
                total_invalid_rows
            )
            print(
                "Clean rows:",
                len(clean_df)
            )

            # --------------------------------------------------
            # 11. Calculate profit
            # --------------------------------------------------

            clean_df = calculate_profit(clean_df)

            print("\nProfit calculation:")
            print(
                clean_df[
                    ["revenue", "expense", "profit"]
                ]
            )

            # --------------------------------------------------
            # 12. Load clean records
            # --------------------------------------------------

            records_loaded = load_finance_records(
                db=db,
                df=clean_df,
                dataset_id=dataset.id
            )

            print("\nDatabase loading:")
            print(
                "Records loaded:",
                records_loaded
            )

            # --------------------------------------------------
            # 13. Calculate metadata
            # --------------------------------------------------

            metadata_data = calculate_metadata(
                original_rows=original_rows,
                cleaned_rows=len(clean_df),
                duplicates_removed=duplicates_removed,
                invalid_rows=total_invalid_rows
            )

            # --------------------------------------------------
            # 14. Save metadata
            # --------------------------------------------------

            metadata = Metadata(
                dataset_id=dataset.id,
                total_rows=metadata_data["total_rows"],
                cleaned_rows=metadata_data["cleaned_rows"],
                duplicates_removed=metadata_data[
                    "duplicates_removed"
                ],
                invalid_rows=metadata_data["invalid_rows"],
                data_quality_score=metadata_data[
                    "data_quality_score"
                ],
                status=metadata_data["status"]
            )

            db.add(metadata)
            db.commit()
            db.refresh(metadata)

            print("\nMetadata:")
            print(
                "Total rows:",
                metadata.total_rows
            )
            print(
                "Cleaned rows:",
                metadata.cleaned_rows
            )
            print(
                "Duplicates removed:",
                metadata.duplicates_removed
            )
            print(
                "Invalid rows:",
                metadata.invalid_rows
            )
            print(
                "Data quality score:",
                metadata.data_quality_score
            )
            print(
                "Status:",
                metadata.status
            )

            # --------------------------------------------------
            # 15. Update dataset status
            # --------------------------------------------------

            dataset.status = "completed"

            db.commit()

            print(
                "\nETL completed successfully."
            )

            # --------------------------------------------------
            # 16. Return API response
            # --------------------------------------------------

            return {
                "status": "completed",
                "dataset_id": dataset.id,
                "filename": dataset.file_name,
                "file_type": dataset.file_type,
                "records_loaded": records_loaded,
                "duplicates_removed": duplicates_removed,
                "invalid_financial_rows": len(
                    invalid_finance_rows
                ),
                "invalid_date_rows": len(
                    invalid_date_rows
                ),
                "invalid_rows": total_invalid_rows,
                "clean_rows": len(clean_df),
                "data_quality_score": (
                    metadata.data_quality_score
                )
            }

    except HTTPException:
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()