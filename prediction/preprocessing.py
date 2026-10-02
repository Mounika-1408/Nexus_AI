import pandas as pd
from pathlib import Path


class DataPreprocessor:
    def __init__(self, input_path, output_path):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)

    def load_data(self):
        """Load the raw sales dataset."""

        if not self.input_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.input_path}"
            )

        df = pd.read_csv(self.input_path)

        print("Dataset loaded successfully.")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")

        return df

    def clean_data(self, df):
        """Clean and validate the sales dataset."""

        print("\n========== Data Cleaning ==========")

        # Standardize column names
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )

        print("\nColumns:")
        print(list(df.columns))

        # Expected columns
        required_columns = [
            "tv",
            "radio",
            "newspaper",
            "sales"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Required columns are missing: {missing_columns}"
            )

        # Keep only required columns
        df = df[required_columns]

        # Convert all columns to numeric
        for column in required_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        # Check missing values before cleaning
        missing_before = df.isnull().sum().sum()

        print(f"\nMissing values before cleaning: {missing_before}")

        # Remove rows containing invalid/missing values
        if missing_before > 0:
            df = df.dropna()

        # Remove duplicate records
        duplicates_before = df.duplicated().sum()

        df = df.drop_duplicates()

        print(f"Duplicates removed: {duplicates_before}")

        # Check missing values after cleaning
        missing_after = df.isnull().sum().sum()

        print(f"Missing values after cleaning: {missing_after}")

        print(f"\nFinal rows: {len(df)}")
        print(f"Final columns: {len(df.columns)}")

        return df

    def save_data(self, df):
        """Save the cleaned dataset."""

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            self.output_path,
            index=False
        )

        print("\nProcessed dataset saved to:")
        print(self.output_path)

    def preprocess(self):
        """Run the complete preprocessing pipeline."""

        df = self.load_data()

        df = self.clean_data(df)

        self.save_data(df)

        return df


if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent.parent

    input_path = (
        BASE_DIR
        / "datasets"
        / "raw"
        / "sales_data_file.csv"
    )

    output_path = (
        BASE_DIR
        / "datasets"
        / "processed"
        / "sales_clean.csv"
    )

    processor = DataPreprocessor(
        input_path,
        output_path
    )

    processor.preprocess()