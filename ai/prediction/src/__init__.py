"""
NexusAI - Sales Prediction Module
"""

from .data_loader import load_sales_data, inspect_dataset
from .preprocessing import preprocess_data, prepare_features
from .evaluate import evaluate_predictions, print_metrics
from .predict import SalesPredictor, predict_sales

__all__ = [
    "load_sales_data",
    "inspect_dataset",
    "preprocess_data",
    "prepare_features",
    "evaluate_predictions",
    "print_metrics",
    "SalesPredictor",
    "predict_sales",
]
