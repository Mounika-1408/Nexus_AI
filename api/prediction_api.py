from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# ============================================================
# Prediction Module Path
# ============================================================

PREDICTION_DIR = (
    Path(__file__).resolve().parent.parent
    / "prediction"
)

sys.path.append(str(PREDICTION_DIR))

from predict import predict_sales


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="NexusAI Prediction API",
    description="API for AI-powered sales prediction",
    version="1.0.0"
)


# ============================================================
# Request Model
# ============================================================

class SalesPredictionRequest(BaseModel):
    tv: float
    radio: float
    newspaper: float


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():
    return {
        "message": "NexusAI Prediction API is running"
    }


# ============================================================
# Sales Prediction Endpoint
# ============================================================

@app.post("/ai/predict/sales")
def sales_prediction(
    request: SalesPredictionRequest
):

    try:

        predicted_sales = predict_sales(
            tv=request.tv,
            radio=request.radio,
            newspaper=request.newspaper
        )

        return {
            "tv": request.tv,
            "radio": request.radio,
            "newspaper": request.newspaper,
            "predicted_sales": round(
                float(predicted_sales),
                2
            )
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )