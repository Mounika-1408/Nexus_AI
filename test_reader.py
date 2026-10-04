from app.models.dataset import Dataset
from app.database.connection import SessionLocal
from app.services.etl.loader import load_finance_records
from app.services.etl.validator import validate_finance_data,remove_invalid_finance_rows
from app.services.etl.metadata import calculate_metadata
from app.services.etl.reader import read_csv
from app.services.etl.cleaner import (
    clean_categories,
    remove_duplicates,
    handle_missing_values,
    convert_numeric_columns,
    calculate_profit
)
file_path = "uploads/amazon_finance_raw.csv"

df = read_csv(file_path)

original_rows = len(df)

print("Original rows:", original_rows)

df = clean_categories(df)

df, removed = remove_duplicates(df)
df = convert_numeric_columns(df)
print("\nMissing values after numeric conversion:")
print(df[["revenue", "expense"]].isnull().sum())

df = handle_missing_values(df)
print("\nMissing values after handling:")
print(df[["revenue", "expense"]].isnull().sum())

errors = validate_finance_data(df)

print("\nValidation errors:")

if errors:
    for error in errors:
        print("-", error)
else:
    print("No validation errors.")

clean_df, invalid_rows = remove_invalid_finance_rows(df)

print("\nInvalid rows:")
print(invalid_rows)

print("\nClean rows:", len(clean_df))
print("Invalid rows:", len(invalid_rows))

clean_df, invalid_rows = remove_invalid_finance_rows(df)

clean_df = calculate_profit(clean_df)

print("\nClean financial data:")
print(clean_df[["revenue", "expense", "profit", "category"]])

clean_df, invalid_rows = remove_invalid_finance_rows(df)

clean_df = calculate_profit(clean_df)

metadata = calculate_metadata(
    original_rows=original_rows,
    cleaned_rows=len(clean_df),
    duplicates_removed=removed,
    invalid_rows=len(invalid_rows)
)

print("\nETL Metadata:")
for key, value in metadata.items():
    print(f"{key}: {value}")

db = SessionLocal()

try:
    dataset_id = 1

    inserted = load_finance_records(
        db=db,
        df=clean_df,
        dataset_id=dataset_id
    )

    print("\nPostgreSQL:")
    print("Records inserted:", inserted)

finally:
    db.close()