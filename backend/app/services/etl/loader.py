from sqlalchemy.orm import Session

from app.models.finance_record import FinanceRecord


def load_finance_records(db: Session, df, dataset_id: int, replace: bool = False):
    existing = db.query(FinanceRecord).filter(FinanceRecord.dataset_id == dataset_id)
    existing_count = existing.count()

    if existing_count > 0:
        if not replace:
            return 0
        # Idempotent cleanup of existing records for this dataset
        existing.delete(synchronize_session=False)

    records = []

    for _, row in df.iterrows():
        # Derive original revenue/expense if not already present
        orig_rev = float(row.get("original_revenue", row["revenue"]))
        orig_exp = float(row.get("original_expense", row.get("expenses", row.get("expense", 0.0))))
        curr = str(row.get("currency", "USD")).strip().upper()
        rate = float(row.get("exchange_rate", 1.0))

        record = FinanceRecord(
            dataset_id=dataset_id,
            date=str(row["date"]),
            revenue=float(row["revenue"]),
            expenses=float(row.get("expenses", row.get("expense", 0.0))),
            profit=float(row["profit"]),
            category=str(row["category"]),
            currency=curr,
            original_revenue=orig_rev,
            original_expenses=orig_exp,
            exchange_rate=rate
        )

        records.append(record)

    db.add_all(records)
    db.commit()

    return len(records)