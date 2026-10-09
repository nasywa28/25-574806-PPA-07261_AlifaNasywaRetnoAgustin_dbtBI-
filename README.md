README - INSTRUKSI SETUP DAN MENJALANKAN PROJECT
TRANSFORMASI DATA DENGAN dbt DAN DASHBOARD BI
================================================

Nama : Alifa Nasywa Retno Agustin
NIM  : 25/574806/PPA/07261

1. DESKRIPSI SINGKAT
--------------------
Data transaksi e-commerce dari project Airflow digunakan sebagai
sumber raw, kemudian dimuat ke DuckDB, dibersihkan serta ditransformasikan
menggunakan dbt, diuji kualitas datanya, dan diekspor ke CSV untuk digunakan
pada dashboard Power BI Desktop.

Alur project:

transaksi.csv
    -> raw.transaksi di warehouse.duckdb
    -> stg_transaksi
    -> mart_daily_sales / mart_product_sales / mart_dashboard_sales
    -> file CSV export
    -> dashboard Power BI


2. PERSYARATAN
--------------
Perangkat dan aplikasi yang diperlukan:

- Windows 10 atau Windows 11 64-bit
- Python
- Visual Studio Code
- Git
- Power BI Desktop
- Koneksi internet untuk instalasi package

Package Python yang digunakan:

- dbt-core
- dbt-duckdb
- duckdb
- pandas


3. SETUP AWAL PROJECT
---------------------
Buka PowerShell, lalu masuk ke folder utama project:

cd C:\Users\HP\tugas_dbt_bi_574806

Buat virtual environment:

python -m venv .venv

Aktifkan virtual environment:

.\.venv\Scripts\Activate.ps1

Jika PowerShell menolak aktivasi script, jalankan:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Kemudian aktifkan kembali:

.\.venv\Scripts\Activate.ps1

Jika berhasil, prompt terminal diawali dengan (.venv).


4. INSTALASI DEPENDENCY
-----------------------
Perbarui pip dan alat build:

python -m pip install --upgrade pip setuptools wheel

Instal dependency project:

python -m pip install "dbt-core<2" "dbt-duckdb<1.11" duckdb pandas

Periksa instalasi:

dbt --version
python -c "import duckdb; print('DuckDB:', duckdb.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"

Alternatif menggunakan requirements.txt:

python -m pip install -r requirements.txt

Contoh isi requirements.txt:

dbt-core<2
dbt-duckdb<1.11
duckdb
pandas


5. MENYIAPKAN DATASET
---------------------
Salin dataset transaksi dari project Airflow ke:

data\transaksi.csv

Dataset minimal memiliki kolom:

- transaction_id
- transaction_date
- product_name
- category
- quantity
- unit_price
- customer_city

Dataset yang digunakan berisi minimal 200 record dan memiliki kolom tanggal.


6. MEMUAT DATA RAW KE DUCKDB
----------------------------
Pastikan terminal berada pada folder utama project:

cd C:\Users\HP\tugas_dbt_bi_574806

Jalankan script pemuatan data:

python scripts\load_raw_to_duckdb.py

Script tersebut akan:

1. Membaca data\transaksi.csv.
2. Membuat data\warehouse.duckdb jika belum ada.
3. Membuat schema raw.
4. Membuat atau mengganti tabel raw.transaksi.
5. Menampilkan jumlah data, null, dan potensi duplikasi.

Hasil yang harus tersedia:

data\warehouse.duckdb


7. KONFIGURASI profiles.yml
---------------------------
File profiles.yml disimpan pada:

dbt_project\profiles.yml

Contoh isi:

dbt_tugas:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: ../data/warehouse.duckdb
      schema: main
      threads: 4

Penting:
- Nama profile "dbt_tugas" harus sama dengan nilai profile pada dbt_project.yml.
- Gunakan spasi, bukan tab.
- Path database dihitung relatif dari lokasi profiles.yml.


8. KONFIGURASI dbt_project.yml
------------------------------
File dbt_project.yml disimpan pada:

dbt_project\dbt_project.yml

Contoh konfigurasi utama:

name: "dbt_tugas"
version: "1.0.0"
config-version: 2
profile: "dbt_tugas"

model-paths:
  - "models"

test-paths:
  - "tests"

clean-targets:
  - "target"
  - "dbt_packages"

models:
  dbt_tugas:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts

Materialization:
- Model staging dibuat sebagai view.
- Model mart dibuat sebagai table.


9. MENJALANKAN DAN MEMERIKSA dbt
---------------------------------
Masuk ke folder dbt_project:

cd C:\Users\HP\tugas_dbt_bi_574806\dbt_project

Periksa konfigurasi dan koneksi:

dbt debug --profiles-dir .

Hasil yang diharapkan:

All checks passed!



10. MENJALANKAN MODEL dbt
-------------------------
Dari folder dbt_project, jalankan:

dbt run --profiles-dir .

Perintah tersebut membangun:

- source raw.transaksi sebagai sumber
- stg_transaksi sebagai staging view
- mart_daily_sales sebagai mart penjualan harian
- mart_product_sales sebagai mart penjualan per produk
- mart_dashboard_sales sebagai mart khusus dashboard

Jika ingin menjalankan satu model saja:

dbt run --select mart_dashboard_sales --profiles-dir .

Jika model berhasil, ringkasan terminal menampilkan PASS dan ERROR=0.


11. MENJALANKAN TEST dbt
------------------------
Jalankan seluruh generic test dan singular test:

dbt test --profiles-dir .

Test yang digunakan meliputi:

- not_null pada kolom penting
- unique pada transaction_id atau kolom kunci yang sesuai
- singular test untuk mendeteksi quantity <= 0, unit_price < 0,
  atau total_amount < 0

Jika run dan test ingin dijalankan sekaligus:

dbt build --profiles-dir .

Project harus dapat menjalankan dbt run dan dbt test berulang kali tanpa error.


12. ANALISIS DAMPAK KUALITAS DATA
---------------------------------
Kembali ke folder utama:

cd ..

Jalankan:

python scripts\analyze_data_quality.py

Script tersebut membandingkan:

- jumlah record raw
- nilai kosong pada kolom penting
- transaction_id duplikat
- record duplikat persis
- quantity tidak valid
- unit_price negatif
- jumlah record staging setelah pembersihan
- jumlah dan persentase record yang dihapus

Simpan hasil ke file teks sekaligus tampilkan di terminal:

python scripts\analyze_data_quality.py | Tee-Object -FilePath data_quality_result.txt



13. MEMBUAT DOKUMENTASI dbt
---------------------------
Masuk kembali ke folder dbt_project:

cd dbt_project

Generate dbt docs:

dbt docs generate --profiles-dir .

Jalankan dokumentasi lokal pada port 8081:

dbt docs serve --profiles-dir . --port 8081

Buka alamat lokal yang ditampilkan terminal melalui browser.

Untuk memeriksa dependency model melalui terminal:

dbt ls --profiles-dir . --select +mart_daily_sales

dbt ls --profiles-dir . --select +mart_dashboard_sales

Dependency yang diharapkan:

raw.transaksi
    -> stg_transaksi
    -> mart_daily_sales / mart_dashboard_sales


14. MENGEKSPOR MART KE CSV
--------------------------
Kembali ke folder utama:

cd ..

Jalankan:

python scripts\export_marts.py

Hasil export disimpan ke:

data\exports\mart_daily_sales.csv
data\exports\mart_product_sales.csv
data\exports\mart_dashboard_sales.csv

Untuk dashboard yang lebih mudah, gunakan mart_dashboard_sales.csv karena berisi:

- transaction_date
- product_name
- category
- total_transactions
- total_quantity
- total_sales
- average_transaction_value


15. MEMBUAT DASHBOARD POWER BI
------------------------------
Buka Power BI Desktop dan buat report baru.

Impor mart dashboard:

Home -> Get data -> Text/CSV

Pilih:

data\exports\mart_dashboard_sales.csv

Pilih Transform Data, lalu pastikan tipe data:

- transaction_date            : Date
- product_name                : Text
- category                    : Text
- total_transactions          : Whole Number
- total_quantity              : Whole Number
- total_sales                 : Decimal Number atau Fixed Decimal Number
- average_transaction_value   : Decimal Number atau Fixed Decimal Number

Pilih Close & Apply.


16. MEMBUAT MEASURE POWER BI
----------------------------
Pada tabel mart_dashboard_sales, buat measure berikut:

Total Penjualan =
SUM(mart_dashboard_sales[total_sales])

Total Transaksi =
SUM(mart_dashboard_sales[total_transactions])

Total Unit =
SUM(mart_dashboard_sales[total_quantity])

Rata-rata Transaksi =
DIVIDE(
    [Total Penjualan],
    [Total Transaksi],
    0
)

Gunakan satu measure untuk satu Card. Jangan memasukkan semua kolom numerik
ke satu visual karena seluruh nilai akan diagregasi dalam chart yang sama.


17. SUSUNAN VISUAL DASHBOARD
----------------------------
Dashboard minimal memuat:

A. KPI Card
- Total Penjualan
- Total Transaksi
- Total Unit
- Rata-rata Transaksi

B. Line Chart - Tren Penjualan Harian
- X-axis : transaction_date
- Y-axis : Total Penjualan

C. Clustered Bar Chart - Penjualan per Produk
- Y-axis : product_name
- X-axis : Total Penjualan
- Urutkan berdasarkan Total Penjualan secara descending.

D. Donut Chart - Kontribusi per Kategori
- Legend : category
- Values : Total Penjualan

E. Slicer
- category, atau
- transaction_date dengan tipe Between


18. MENJALANKAN ULANG PROJECT DARI AWAL
---------------------------------------
Urutan lengkap dari folder utama:

.\.venv\Scripts\Activate.ps1
python scripts\load_raw_to_duckdb.py
cd dbt_project
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .
dbt docs generate --profiles-dir .
cd ..
python scripts\analyze_data_quality.py
python scripts\export_marts.py

Setelah export selesai, buka file Power BI dan pilih Refresh apabila sumber CSV
masih menggunakan lokasi yang sama.


