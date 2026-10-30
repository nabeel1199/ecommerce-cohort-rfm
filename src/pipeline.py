"""Run every SQL file in order against the raw data and export the results.

Usage:
    python src/pipeline.py

All analysis lives in the numbered files under sql/. This script only wires
them together: it registers the raw Parquet file as a view, executes each
SQL file in order, and exports the result tables to CSV (used by the
notebook, the dashboard, and the Tableau guide).
"""
from pathlib import Path
from typing import Optional

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "online_retail_ii.parquet"
SQL_DIR = ROOT / "sql"
EXPORTS = ROOT / "exports"

# Result tables worth exporting (the intermediate tables stay in DuckDB).
EXPORT_TABLES = [
    "headline_kpis",
    "data_quality",
    "monthly_kpis",
    "cohort_retention",
    "retention_summary",
    "repeat_rate",
    "rfm",
    "rfm_segments",
    "customer_pareto",
    "country_revenue",
    "product_performance",
    "cancellation_summary",
    "order_timing",
]


def build(con: Optional[duckdb.DuckDBPyConnection] = None) -> duckdb.DuckDBPyConnection:
    if not RAW.exists():
        raise SystemExit("Raw data missing - run `python scripts/download_data.py` first.")
    con = con or duckdb.connect()
    con.execute(f"CREATE OR REPLACE VIEW raw_retail AS SELECT * FROM read_parquet('{RAW.as_posix()}')")
    for sql_file in sorted(SQL_DIR.glob("*.sql")):
        con.execute(sql_file.read_text())
    return con


def export(con: duckdb.DuckDBPyConnection) -> None:
    EXPORTS.mkdir(exist_ok=True)
    for table in EXPORT_TABLES:
        con.table(table).df().to_csv(EXPORTS / f"{table}.csv", index=False)


if __name__ == "__main__":
    connection = build()
    export(connection)
    print(f"Exported {len(EXPORT_TABLES)} tables to {EXPORTS}")
    print(connection.table("data_quality").df().to_string(index=False))
