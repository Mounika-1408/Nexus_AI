from sqlalchemy.orm import Session

from app.models.finance_record import FinanceRecord


def load_finance_records(db: Session, df, dataset_id: int):

    existing_count = (
        db.query(FinanceRecord)
        .filter(FinanceRecord.dataset_id == dataset_id)
        .count()
    )

    if existing_count > 0:
        return 0

    records = []

    for _, row in df.iterrows():

        record = FinanceRecord(
            dataset_id=dataset_id,
            date=str(row["date"]),
            revenue=float(row["revenue"]),
            expenses=float(row["expense"]),
            profit=float(row["profit"]),
            category=str(row["category"])
        )

        records.append(record)

    db.add_all(records)
    db.commit()

    return len(records)