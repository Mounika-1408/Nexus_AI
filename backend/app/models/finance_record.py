from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.database.base import Base


class FinanceRecord(Base):
    __tablename__ = "finance_records"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False
    )

    date = Column(String(50), nullable=False)

    revenue = Column(Float, nullable=True)

    expenses = Column(Float, nullable=True)

    profit = Column(Float, nullable=True)

    category = Column(String(100), nullable=True)

    currency = Column(String(10), nullable=True)

    original_revenue = Column(Float, nullable=True)

    original_expenses = Column(Float, nullable=True)

    exchange_rate = Column(Float, nullable=True, default=1.0)