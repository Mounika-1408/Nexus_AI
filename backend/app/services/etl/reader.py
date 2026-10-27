import pandas as pd


def read_csv(file_path: str):
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    return pd.read_csv(file_path)


def read_excel(file_path: str):
    df = pd.read_excel(file_path)
    return df