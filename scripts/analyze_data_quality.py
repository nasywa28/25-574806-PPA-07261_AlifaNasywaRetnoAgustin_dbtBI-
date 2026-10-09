from pathlib import Path

import duckdb


# ============================================================
# KONFIGURASI PATH
# ============================================================

BASE_PATH = Path(__file__).resolve().parent.parent

DATABASE_FILE = (
    BASE_PATH
    / "data"
    / "warehouse.duckdb"
)


# ============================================================
# FUNGSI UTAMA
# ============================================================

def analyze_data_quality():
    """
    Membandingkan kualitas data sebelum dan sesudah
    proses pembersihan pada model staging dbt.
    """

    # Memastikan file DuckDB tersedia
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database DuckDB tidak ditemukan: {DATABASE_FILE}"
        )

    print("=" * 65)
    print("ANALISIS DAMPAK KUALITAS DATA")
    print("=" * 65)

    print(f"Database: {DATABASE_FILE}")

    # Membuka koneksi ke DuckDB
    connection = duckdb.connect(
        str(DATABASE_FILE)
    )

    # ========================================================
    # 1. MENAMPILKAN DAFTAR SCHEMA
    # ========================================================

    print("\n1. DAFTAR SCHEMA DALAM DATABASE")
    print("-" * 65)

    schemas = connection.execute(
        """
        SELECT
            schema_name

        FROM information_schema.schemata

        ORDER BY schema_name
        """
    ).fetchall()

    for schema in schemas:
        print(f"- {schema[0]}")

    # ========================================================
    # 2. MENAMPILKAN TABEL DAN VIEW
    # ========================================================

    print("\n2. DAFTAR TABEL DAN VIEW")
    print("-" * 65)

    relations = connection.execute(
        """
        SELECT
            table_schema,
            table_name,
            table_type

        FROM information_schema.tables

        WHERE table_schema NOT IN (
            'information_schema',
            'pg_catalog'
        )

        ORDER BY
            table_schema,
            table_name
        """
    ).fetchall()

    for schema_name, table_name, table_type in relations:
        print(
            f"- {schema_name}.{table_name} "
            f"({table_type})"
        )

    # ========================================================
    # 3. MEMASTIKAN TABEL RAW TERSEDIA
    # ========================================================

    raw_table_exists = connection.execute(
        """
        SELECT COUNT(*)

        FROM information_schema.tables

        WHERE table_schema = 'raw'
          AND table_name = 'transaksi'
        """
    ).fetchone()[0]

    if raw_table_exists == 0:
        connection.close()

        raise ValueError(
            "Tabel raw.transaksi tidak ditemukan. "
            "Jalankan scripts/load_raw_to_duckdb.py terlebih dahulu."
        )

    # ========================================================
    # 4. MENCARI MODEL STAGING SECARA OTOMATIS
    # ========================================================

    staging_result = connection.execute(
        """
        SELECT
            table_schema,
            table_name

        FROM information_schema.tables

        WHERE table_name = 'stg_transaksi'

        ORDER BY table_schema

        LIMIT 1
        """
    ).fetchone()

    if staging_result is None:
        connection.close()

        raise ValueError(
            "Model stg_transaksi tidak ditemukan. "
            "Jalankan dbt run terlebih dahulu."
        )

    staging_schema = staging_result[0]
    staging_table = staging_result[1]

    staging_relation = (
        f'"{staging_schema}"."{staging_table}"'
    )

    print("\n3. MODEL STAGING YANG DIGUNAKAN")
    print("-" * 65)

    print(
        f"Model ditemukan pada: "
        f"{staging_schema}.{staging_table}"
    )

    # ========================================================
    # 5. MENGHITUNG JUMLAH DATA RAW
    # ========================================================

    total_raw_records = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi
        """
    ).fetchone()[0]

    # ========================================================
    # 6. MENGHITUNG NILAI KOSONG
    # ========================================================

    null_transaction_id = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE transaction_id IS NULL
        """
    ).fetchone()[0]

    null_transaction_date = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE transaction_date IS NULL
        """
    ).fetchone()[0]

    null_product_name = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE product_name IS NULL
        """
    ).fetchone()[0]

    null_quantity = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE quantity IS NULL
        """
    ).fetchone()[0]

    null_unit_price = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE unit_price IS NULL
        """
    ).fetchone()[0]

    total_null_values = (
        null_transaction_id
        + null_transaction_date
        + null_product_name
        + null_quantity
        + null_unit_price
    )

    # ========================================================
    # 7. MENGHITUNG TRANSACTION_ID DUPLIKAT
    # ========================================================

    duplicate_transaction_ids = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(record_count - 1),
                0
            )

        FROM (
            SELECT
                transaction_id,
                COUNT(*) AS record_count

            FROM raw.transaksi

            GROUP BY transaction_id

            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    # ========================================================
    # 8. MENGHITUNG BARIS DUPLIKAT PERSIS
    # ========================================================

    exact_duplicate_records = connection.execute(
        """
        SELECT
            COALESCE(
                SUM(record_count - 1),
                0
            )

        FROM (
            SELECT
                transaction_id,
                transaction_date,
                product_name,
                category,
                quantity,
                unit_price,
                customer_city,
                COUNT(*) AS record_count

            FROM raw.transaksi

            GROUP BY
                transaction_id,
                transaction_date,
                product_name,
                category,
                quantity,
                unit_price,
                customer_city

            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    # ========================================================
    # 9. MENGHITUNG NILAI NUMERIK TIDAK VALID
    # ========================================================

    invalid_quantity = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE quantity <= 0
        """
    ).fetchone()[0]

    negative_unit_price = connection.execute(
        """
        SELECT COUNT(*)

        FROM raw.transaksi

        WHERE unit_price < 0
        """
    ).fetchone()[0]

    # ========================================================
    # 10. MENGHITUNG RECORD SETELAH STAGING
    # ========================================================

    total_staging_records = connection.execute(
        f"""
        SELECT COUNT(*)

        FROM {staging_relation}
        """
    ).fetchone()[0]

    # ========================================================
    # 11. MENGHITUNG RECORD YANG DIHAPUS
    # ========================================================

    removed_records = (
        total_raw_records
        - total_staging_records
    )

    if total_raw_records > 0:
        removed_percentage = (
            removed_records
            / total_raw_records
            * 100
        )
    else:
        removed_percentage = 0

    # ========================================================
    # 12. VALIDASI DATA SETELAH STAGING
    # ========================================================

    staging_null_products = connection.execute(
        f"""
        SELECT COUNT(*)

        FROM {staging_relation}

        WHERE product_name IS NULL
        """
    ).fetchone()[0]

    staging_duplicate_ids = connection.execute(
        f"""
        SELECT
            COALESCE(
                SUM(record_count - 1),
                0
            )

        FROM (
            SELECT
                transaction_id,
                COUNT(*) AS record_count

            FROM {staging_relation}

            GROUP BY transaction_id

            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    staging_invalid_values = connection.execute(
        f"""
        SELECT COUNT(*)

        FROM {staging_relation}

        WHERE quantity <= 0
           OR unit_price < 0
           OR total_amount < 0
        """
    ).fetchone()[0]

    # ========================================================
    # 13. MENAMPILKAN HASIL
    # ========================================================

    print("\n4. KUALITAS DATA SEBELUM PEMBERSIHAN")
    print("-" * 65)

    print(
        f"Jumlah record raw               : "
        f"{total_raw_records}"
    )

    print(
        f"Null transaction_id             : "
        f"{null_transaction_id}"
    )

    print(
        f"Null transaction_date           : "
        f"{null_transaction_date}"
    )

    print(
        f"Null product_name               : "
        f"{null_product_name}"
    )

    print(
        f"Null quantity                   : "
        f"{null_quantity}"
    )

    print(
        f"Null unit_price                 : "
        f"{null_unit_price}"
    )

    print(
        f"Total nilai kosong kolom penting: "
        f"{total_null_values}"
    )

    print(
        f"Transaction ID duplikat         : "
        f"{duplicate_transaction_ids}"
    )

    print(
        f"Record duplikat persis          : "
        f"{exact_duplicate_records}"
    )

    print(
        f"Quantity tidak valid            : "
        f"{invalid_quantity}"
    )

    print(
        f"Unit price negatif              : "
        f"{negative_unit_price}"
    )

    print("\n5. KUALITAS DATA SETELAH PEMBERSIHAN")
    print("-" * 65)

    print(
        f"Jumlah record staging           : "
        f"{total_staging_records}"
    )

    print(
        f"Null product_name setelah staging: "
        f"{staging_null_products}"
    )

    print(
        f"Transaction ID duplikat staging : "
        f"{staging_duplicate_ids}"
    )

    print(
        f"Nilai numerik tidak valid       : "
        f"{staging_invalid_values}"
    )

    print("\n6. DAMPAK PEMBERSIHAN DATA")
    print("-" * 65)

    print(
        f"Sebelum pembersihan             : "
        f"{total_raw_records} record"
    )

    print(
        f"Setelah pembersihan             : "
        f"{total_staging_records} record"
    )

    print(
        f"Jumlah record yang dihapus      : "
        f"{removed_records} record"
    )

    print(
        f"Persentase record yang dihapus  : "
        f"{removed_percentage:.2f}%"
    )

    print("=" * 65)

    connection.close()


if __name__ == "__main__":
    analyze_data_quality()