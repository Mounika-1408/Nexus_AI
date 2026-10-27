from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.prediction_service import predict_sales_service, get_model_info_service

router = APIRouter(
    prefix="/ai",
    tags=["AI Prediction"]
)

class SalesPredictionRequest(BaseModel):
    tv: float = Field(..., description="TV advertising expenditure in $k", ge=0)
    radio: float = Field(..., description="Radio advertising expenditure in $k", ge=0)
    newspaper: float = Field(..., description="Newspaper advertising expenditure in $k", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "tv": 180.8,
                "radio": 10.8,
                "newspaper": 58.4
            }
        }

class SalesPredictionResponse(BaseModel):
    tv: float
    radio: float
    newspaper: float
    predicted_sales: float
    is_extrapolating: Optional[bool] = False
    extrapolation_warning: Optional[str] = None
    model_name: Optional[str] = None
    units: Optional[str] = None

@router.get(
    "/predict/sales/model-info",
    status_code=status.HTTP_200_OK,
    summary="Get Advertising ML Model Card & Evaluation Metrics",
    description="Returns cross-validation metrics, test metrics, and training feature ranges from metrics.json."
)
def get_model_info_endpoint():
    try:
        return get_model_info_service()
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching model metrics: {str(e)}"
        )

@router.post(
    "/predict/sales",
    response_model=SalesPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Sales from Advertising Expenditures",
    description="Predict total product sales based on TV, Radio, and Newspaper advertising budgets."
)
def predict_sales_endpoint(payload: SalesPredictionRequest):
    try:
        result = predict_sales_service(
            tv=payload.tv,
            radio=payload.radio,
            newspaper=payload.newspaper
        )
        return result
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing sales prediction: {str(e)}"
        )


class RevenueForecastRequest(BaseModel):
    dataset_id: int = Field(..., description="ID of the uploaded dataset in PostgreSQL", ge=1)
    horizon_days: int = Field(30, description="Forecast horizon in days (7, 30, or 90)")
    anchor_date: Optional[str] = Field(None, description="Optional ISO anchor date (YYYY-MM-DD). Defaults to current date.")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 1,
                "horizon_days": 30,
                "anchor_date": "2026-10-24"
            }
        }


@router.post(
    "/forecast/revenue",
    status_code=status.HTTP_200_OK,
    summary="Financial Revenue Forecasting",
    description="Forecast future daily revenue based on actual date and revenue records from an uploaded dataset."
)
def forecast_revenue_endpoint(payload: RevenueForecastRequest):
    try:
        from app.services.forecasting_service import forecast_revenue_service
        result = forecast_revenue_service(
            dataset_id=payload.dataset_id,
            horizon_days=payload.horizon_days,
            anchor_date=payload.anchor_date
        )
        return result
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating revenue forecast: {str(e)}"
        )
