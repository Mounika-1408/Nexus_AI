import os
import sys
import argparse
import joblib
import pandas as pd
from typing import Dict, Union

# Add parent dir to sys.path for relative imports if called directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preprocessing import prepare_features

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models"
)

MODEL_PATH = os.path.join(MODELS_DIR, "best_model.joblib")
PREPROCESSOR_PATH = os.path.join(MODELS_DIR, "preprocessor.joblib")

class SalesPredictor:
    """
    Sales Prediction service class for NexusAI. Loads saved model & preprocessor and provides inference API.
    """
    def __init__(self, model_path: str = MODEL_PATH, preprocessor_path: str = PREPROCESSOR_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please run train.py first.")
        if not os.path.exists(preprocessor_path):
            raise FileNotFoundError(f"Preprocessor file not found at {preprocessor_path}. Please run train.py first.")

        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)

    def predict(self, tv: float, radio: float, newspaper: float) -> Dict[str, Union[float, Dict[str, float]]]:
        """
        Accept TV, Radio, Newspaper advertising expenditures and return predicted Sales.
        """
        input_data = {"TV": float(tv), "Radio": float(radio), "Newspaper": float(newspaper)}
        df_input = prepare_features(input_data, feature_names=self.preprocessor.feature_names)
        
        # Scale features using fitted scaler
        X_scaled = self.preprocessor.transform(df_input)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)[0]
        
        return {
            "predicted_sales": round(float(prediction), 4),
            "inputs": input_data
        }

def predict_sales(tv: float, radio: float, newspaper: float) -> Dict[str, Union[float, Dict[str, float]]]:
    """
    Convenience standalone function for predicting sales.
    """
    predictor = SalesPredictor()
    return predictor.predict(tv, radio, newspaper)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexusAI Sales Prediction CLI")
    parser.add_argument("--tv", type=float, default=230.1, help="TV advertising budget")
    parser.add_argument("--radio", type=float, default=37.8, help="Radio advertising budget")
    parser.add_argument("--newspaper", type=float, default=69.2, help="Newspaper advertising budget")
    
    args = parser.parse_args()
    
    result = predict_sales(args.tv, args.radio, args.newspaper)
    print("\n" + "="*50)
    print("        NEXUS_AI SALES PREDICTION RESULT        ")
    print("="*50)
    print(f"Inputs          : TV={args.tv}, Radio={args.radio}, Newspaper={args.newspaper}")
    print(f"Predicted Sales : {result['predicted_sales']}")
    print("="*50)
