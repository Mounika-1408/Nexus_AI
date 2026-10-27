import os
import sys
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

TEST_DB_FILE = os.path.join(BACKEND_DIR, "test_isolated_db.sqlite")
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["JWT_SECRET"] = "test_jwt_secret_key_nexusai_testing_only"
os.environ["ENVIRONMENT"] = "testing"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from app.database.base import Base
from app.database import connection
from app.models.user import User
from app.models.company import Company
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord
from app.models.metadata import Metadata
from app.services.auth_service import hash_password, create_access_token


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    test_engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    connection.engine = test_engine
    connection.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Seed Company 1
    session = connection.SessionLocal()
    try:
        company = session.query(Company).filter(Company.id == 1).first()
        if not company:
            company = Company(id=1, name="Nexus Global", industry="Analytics")
            session.add(company)
            session.commit()
    finally:
        session.close()

    yield test_engine

    try:
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_session(init_test_db):
    session = connection.SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    user = db_session.query(User).filter(User.email == "test@nexusai.com").first()
    if not user:
        user = User(
            name="Test User",
            email="test@nexusai.com",
            password=hash_password("Password123!"),
            role="user"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    token = create_access_token({"sub": test_user.email, "uid": test_user.id, "name": test_user.name})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def seeded_dataset(db_session):
    db_session.query(FinanceRecord).filter(FinanceRecord.dataset_id == 100).delete()
    db_session.query(Metadata).filter(Metadata.dataset_id == 100).delete()
    db_session.query(Dataset).filter(Dataset.id == 100).delete()
    db_session.commit()

    dataset = Dataset(
        id=100,
        company_id=1,
        file_name="test_financial_records.csv",
        file_type=".csv",
        file_path="uploads/test_fixture.csv",
        status="completed"
    )
    db_session.add(dataset)
    db_session.commit()

    records = []
    base_date = pd.to_datetime("2026-03-01")
    for i in range(30):
        d_str = (base_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        records.append(
            FinanceRecord(
                dataset_id=100,
                date=d_str,
                category="electronics" if i % 2 == 0 else "apparel",
                revenue=100.0 + (i * 2.0),
                expenses=50.0 + (i * 1.0),
                profit=50.0 + (i * 1.0),
                currency="USD",
                original_revenue=100.0 + (i * 2.0),
                original_expenses=50.0 + (i * 1.0),
                exchange_rate=1.0
            )
        )

    db_session.add_all(records)

    metadata = Metadata(
        dataset_id=100,
        total_rows=30,
        cleaned_rows=30,
        duplicates_removed=0,
        invalid_rows=0,
        data_quality_score=100.0,
        status="completed"
    )
    db_session.add(metadata)
    db_session.commit()

    return dataset
