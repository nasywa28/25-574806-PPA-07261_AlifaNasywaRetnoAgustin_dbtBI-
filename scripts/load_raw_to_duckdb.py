from pathlib import Path

import duckdb
import pandas as pd


BASE_PATH = Path(__file__).resolve().parent.parent

CSV_FILE = BASE_PATH / "data" / "transaksi.csv"
DATABASE_FILE = BASE_PATH / "data" / "warehouse.duckdb"


def load_raw_data():
    """
    Memuat data transaksi CSV ke schema raw pada DuckDB.
    """

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Dataset tidak ditemukan: {CSV_FILE}"
        )

    dataframe = pd.read_csv(CSV_FILE)

    connection = duckdb.connect(str(DATABASE_FILE))

    connection.execute(
        "CREATE SCHEMA IF NOT EXISTS raw"
    )

    connection.register(
        "transaction_dataframe",
        dataframe,
    )

    connection.execute(
        """
        CREATE OR REPLACE TABLE raw.transaksi AS
        SELECT *
        FROM transaction_dataframe
        """
    )

    total_records = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw.transaksi
        """
    ).fetchone()[0]

    null_products = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw.transaksi
        WHERE product_name IS NULL
        """
    ).fetchone()[0]

    duplicate_records = connection.execute(
        """
        SELECT COUNT(*) - COUNT(DISTINCT transaction_id)
        FROM raw.transaksi
        """
    ).fetchone()[0]

    print(
        f"Raw table berhasil dibuat: {total_records} record"
    )

    print(
        f"Nilai kosong product_name: {null_products}"
    )

    print(
        f"Potensi transaction_id duplikat: {duplicate_records}"
    )

    connection.close()


if __name__ == "__main__":
    load_raw_data()