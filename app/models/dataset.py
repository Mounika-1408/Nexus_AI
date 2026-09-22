from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False
    )

    file_name = Column(String(255), nullable=False)

    file_type = Column(String(50), nullable=False)

    file_path = Column(String(500), nullable=False)

    status = Column(String(50), default="uploaded")