from pathlib import Path

import duckdb


BASE_PATH = Path(__file__).resolve().parent.parent

DATABASE_FILE = (
    BASE_PATH
    / "data"
    / "warehouse.duckdb"
)

EXPORT_FOLDER = (
    BASE_PATH
    / "data"
    / "exports"
)


def export_marts():
    """
    Mengekspor tabel mart DuckDB ke CSV untuk Power BI.
    """

    EXPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = duckdb.connect(
        str(DATABASE_FILE)
    )

    tables = connection.execute(
        """
        select
            table_schema,
            table_name

        from information_schema.tables

        where table_name in (
            'mart_daily_sales',
            'mart_product_sales',
            'mart_dashboard_sales'
        )
        """
    ).fetchall()

    if not tables:
        raise ValueError(
            "Model mart belum ditemukan. Jalankan dbt run terlebih dahulu."
        )

    for schema_name, table_name in tables:
        output_file = (
            EXPORT_FOLDER
            / f"{table_name}.csv"
        )

        query = f"""
        copy (
            select *
            from "{schema_name}"."{table_name}"
        )
        to '{output_file.as_posix()}'
        with (
            header true,
            delimiter ','
        )
        """

        connection.execute(query)

        print(
            f"Berhasil mengekspor: {output_file}"
        )

    connection.close()


if __name__ == "__main__":
    export_marts()