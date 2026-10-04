from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.base import Base
from app.database.connection import engine

from app.models.user import User
from app.models.company import Company
from app.models.dataset import Dataset
from app.models.finance_record import FinanceRecord
from app.models.metadata import Metadata

from app.api.upload import router as upload_router
from app.api.datasets import router as datasets_router
from app.api.prediction import router as prediction_router


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
# Create database tables
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# Register API routers
# --------------------------------------------------

app.include_router(upload_router)
app.include_router(datasets_router)
app.include_router(prediction_router)



# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to NexusAI 🚀"
    }