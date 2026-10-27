import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.base import Base
from app.database.connection import engine, SessionLocal

from app.models.user import User
from app.models.company import Company
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord
from app.models.metadata import Metadata

from app.services.auth_service import get_current_user
from app.api.auth import router as auth_router
from app.api.upload import router as upload_router
from app.api.datasets import router as datasets_router
from app.api.prediction import router as prediction_router
from app.api.chat import router as chat_router


app = FastAPI(
    title="NexusAI API",
    description="Backend for NexusAI",
    version="1.0.0"
)


# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Create database tables & Seed initial company (D9)
# --------------------------------------------------

def seed_initial_company():
    """Ensure company ID 1 exists so dataset uploads satisfy foreign key constraint."""
    db = SessionLocal()
    try:
        existing = db.query(Company).filter(Company.id == 1).first()
        if not existing:
            company = Company(id=1, name="Nexus Global", industry="Analytics")
            db.add(company)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def seed_initial_admin_user():
    """Ensure a default demo user exists for seamless first login."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@nexusai.com").first()
        if not existing:
            from app.services.auth_service import hash_password
            admin_user = User(
                name="Administrator",
                email="admin@nexusai.com",
                password=hash_password("admin123"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def init_database_with_retry(max_retries: int = 5, delay: float = 2.0):
    """Initializes tables and seeds initial data with retry for network resilience."""
    import time
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            seed_initial_company()
            seed_initial_admin_user()
            print("Database connected and tables verified.")
            return
        except Exception as e:
            if attempt < max_retries:
                print(f"[Warning] Database connection attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"[Error] Could not connect to database after {max_retries} attempts: {e}")
                raise e

init_database_with_retry()


# --------------------------------------------------
# Register API routers
# --------------------------------------------------

# Public authentication endpoints
app.include_router(auth_router)

# Authenticated business endpoints
app.include_router(
    upload_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    datasets_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    prediction_router,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    chat_router,
    dependencies=[Depends(get_current_user)]
)


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to NexusAI 🚀",
        "status": "online"
    }