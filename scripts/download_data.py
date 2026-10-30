"""Download the UCI Online Retail II dataset and convert it to Parquet.

Source: UCI Machine Learning Repository, "Online Retail II" (CC BY 4.0)
https://archive.ics.uci.edu/dataset/502/online+retail+ii

The original file is a ~45 MB Excel workbook with two sheets
(2009-2010 and 2010-2011). Excel is slow to query, so we read it once and
store a single combined Parquet file that DuckDB can scan in milliseconds.
"""
from pathlib import Path
import urllib.request
import zipfile

import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    zip_path = RAW / "online_retail_ii.zip"
    xlsx_path = RAW / "online_retail_II.xlsx"
    parquet_path = RAW / "online_retail_ii.parquet"

    if not xlsx_path.exists():
        if not zip_path.exists():
            print(f"Downloading {URL} ...")
            urllib.request.urlretrieve(URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(RAW)

    print("Reading both Excel sheets (this takes a few minutes) ...")
    # A handful of Description cells are bare numbers in the source file, so force text columns to str.
    text_cols = {"Invoice": str, "StockCode": str, "Description": str, "Country": str}
    sheets = pd.read_excel(xlsx_path, sheet_name=None, dtype=text_cols)
    df = pd.concat(sheets.values(), ignore_index=True)

    # Normalise column names to snake_case so the SQL reads cleanly.
    df = df.rename(columns={
        "Invoice": "invoice", "StockCode": "stock_code", "Description": "description",
        "Quantity": "quantity", "InvoiceDate": "invoice_date", "Price": "unit_price",
        "Customer ID": "customer_id", "Country": "country",
    })
    df["customer_id"] = df["customer_id"].astype("Int64")
    df.to_parquet(parquet_path, index=False)
    print(f"Saved {len(df):,} rows -> {parquet_path}")


if __name__ == "__main__":
    main()
