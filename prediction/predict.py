from pathlib import Path

import pandas as pd

from utils import load_model


# ============================================================
# Model Path
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "sales_random_forest.pkl"
)


# ============================================================
# Sales Prediction
# ============================================================

def predict_sales(tv, radio, newspaper):

    model = load_model(MODEL_PATH)

    input_data = pd.DataFrame({
        "tv": [tv],
        "radio": [radio],
        "newspaper": [newspaper]
    })

    prediction = model.predict(input_data)

    return prediction[0]


# ============================================================
# Main
# ============================================================

def main():

    print("\n========== NexusAI Sales Prediction ==========\n")

    try:

        tv = float(
            input("Enter TV advertising spend: ")
        )

        radio = float(
            input("Enter Radio advertising spend: ")
        )

        newspaper = float(
            input("Enter Newspaper advertising spend: ")
        )

        predicted_sales = predict_sales(
            tv,
            radio,
            newspaper
        )

        print("\n========== Prediction Result ==========")

        print(
            f"TV Advertising       : {tv:.2f}"
        )

        print(
            f"Radio Advertising    : {radio:.2f}"
        )

        print(
            f"Newspaper Advertising: {newspaper:.2f}"
        )

        print(
            f"\nPredicted Sales      : {predicted_sales:.2f}"
        )

    except ValueError:

        print(
            "\nError: Please enter valid numeric values."
        )

    except FileNotFoundError as error:

        print(f"\nError: {error}")

    except Exception as error:

        print(f"\nUnexpected error: {error}")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()