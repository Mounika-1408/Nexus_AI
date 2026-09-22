from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord
from app.models.metadata import Metadata


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)


# --------------------------------------------------
# GET ALL DATASETS
# --------------------------------------------------

@router.get("/")
def get_datasets():

    db: Session = SessionLocal()

    try:

        datasets = db.query(Dataset).all()

        return [
            {
                "id": dataset.id,
                "company_id": dataset.company_id,
                "file_name": dataset.file_name,
                "file_type": dataset.file_type,
                "file_path": dataset.file_path,
                "status": dataset.status
            }
            for dataset in datasets
        ]

    finally:
        db.close()


# --------------------------------------------------
# GET RECORDS FOR A DATASET
# --------------------------------------------------

@router.get("/{dataset_id}/records")
def get_dataset_records(dataset_id: int):

    db: Session = SessionLocal()

    try:

        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found"
            )

        records = (
            db.query(FinanceRecord)
            .filter(FinanceRecord.dataset_id == dataset_id)
            .all()
        )

        return [
            {
                "id": record.id,
                "dataset_id": record.dataset_id,
                "date": record.date,
                "revenue": record.revenue,
                "expenses": record.expenses,
                "profit": record.profit,
                "category": record.category
            }
            for record in records
        ]

    finally:
        db.close()


# --------------------------------------------------
# GET METADATA FOR A DATASET
# --------------------------------------------------

@router.get("/{dataset_id}/metadata")
def get_dataset_metadata(dataset_id: int):

    db: Session = SessionLocal()

    try:

        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found"
            )

        metadata = (
            db.query(Metadata)
            .filter(Metadata.dataset_id == dataset_id)
            .first()
        )

        if metadata is None:
            raise HTTPException(
                status_code=404,
                detail="Metadata not found for this dataset"
            )

        return {
            "dataset_id": metadata.dataset_id,
            "total_rows": metadata.total_rows,
            "cleaned_rows": metadata.cleaned_rows,
            "duplicates_removed": metadata.duplicates_removed,
            "invalid_rows": metadata.invalid_rows,
            "data_quality_score": metadata.data_quality_score,
            "status": metadata.status
        }

    finally:
        db.close()


# --------------------------------------------------
# GET DATASET SUMMARY
# --------------------------------------------------

@router.get("/{dataset_id}/summary")
def get_dataset_summary(dataset_id: int):

    db: Session = SessionLocal()

    try:

        # Check whether dataset exists
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found"
            )

        # Get all finance records for this dataset
        records = (
            db.query(FinanceRecord)
            .filter(FinanceRecord.dataset_id == dataset_id)
            .all()
        )

        # Calculate summary values
        total_revenue = sum(
            record.revenue or 0
            for record in records
        )

        total_expenses = sum(
            record.expenses or 0
            for record in records
        )

        total_profit = sum(
            record.profit or 0
            for record in records
        )

        # Get metadata
        metadata = (
            db.query(Metadata)
            .filter(Metadata.dataset_id == dataset_id)
            .first()
        )

        return {
            "dataset_id": dataset_id,
            "file_name": dataset.file_name,
            "records": len(records),
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "total_profit": round(total_profit, 2),
            "data_quality_score": (
                metadata.data_quality_score
                if metadata
                else None
            ),
            "status": dataset.status
        }

    finally:
        db.close()