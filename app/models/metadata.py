from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.database.base import Base


class Metadata(Base):
    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False
    )

    total_rows = Column(Integer, default=0)

    cleaned_rows = Column(Integer, default=0)

    duplicates_removed = Column(Integer, default=0)

    invalid_rows = Column(Integer, default=0)

    data_quality_score = Column(Float, nullable=True)

    status = Column(String(50), default="pending")