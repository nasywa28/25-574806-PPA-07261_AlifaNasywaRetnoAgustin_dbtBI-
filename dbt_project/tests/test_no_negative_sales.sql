select
    transaction_id,
    transaction_date,
    quantity,
    unit_price,
    total_amount

from {{ ref('stg_transaksi') }}

where quantity <= 0
   or unit_price < 0
   or total_amount < 0