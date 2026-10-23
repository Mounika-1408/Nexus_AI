from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.prediction_service import predict_sales_service

router = APIRouter(
    prefix="/ai",
    tags=["AI Prediction"]
)

class SalesPredictionRequest(BaseModel):
    tv: float = Field(..., description="TV advertising expenditure", ge=0)
    radio: float = Field(..., description="Radio advertising expenditure", ge=0)
    newspaper: float = Field(..., description="Newspaper advertising expenditure", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "tv": 230.1,
                "radio": 37.8,
                "newspaper": 69.2
            }
        }

class SalesPredictionResponse(BaseModel):
    tv: float
    radio: float
    newspaper: float
    predicted_sales: float

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

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 1,
                "horizon_days": 30
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
            horizon_days=payload.horizon_days
        )
        return result
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating revenue forecast: {str(e)}"
        )

