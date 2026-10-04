import os
import sys
from typing import Dict, Any
from fastapi import HTTPException

# Add project root directory to sys.path if not present
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

MODEL_DIR = os.path.join(PROJECT_ROOT, "ai", "prediction", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model.joblib")
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "preprocessor.joblib")

_predictor_instance = None

def get_predictor():
    """
    Lazy load and cache the SalesPredictor instance from the ai.prediction module.
    """
    global _predictor_instance
    if _predictor_instance is not None:
        return _predictor_instance

    if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
        raise HTTPException(
            status_code=503,
            detail="Sales prediction model artifacts not found. Please train the model before requesting predictions."
        )

    try:
        from ai.prediction.src.predict import SalesPredictor
        _predictor_instance = SalesPredictor(model_path=MODEL_PATH, preprocessor_path=PREPROCESSOR_PATH)
        return _predictor_instance
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load sales prediction model: {str(e)}"
        )

def predict_sales_service(tv: float, radio: float, newspaper: float) -> Dict[str, Any]:
    """
    Service layer function to generate sales predictions given TV, Radio, and Newspaper input features.
    """
    predictor = get_predictor()
    res = predictor.predict(tv=tv, radio=radio, newspaper=newspaper)
    return {
        "tv": tv,
        "radio": radio,
        "newspaper": newspaper,
        "predicted_sales": res["predicted_sales"]
    }
