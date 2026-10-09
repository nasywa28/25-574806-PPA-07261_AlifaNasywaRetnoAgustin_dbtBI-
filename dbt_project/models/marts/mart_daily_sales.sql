with transactions as (

    select *
    from {{ ref('stg_transaksi') }}

)

select
    transaction_date,

    count(distinct transaction_id)
        as total_transactions,

    sum(quantity)
        as total_quantity,

    sum(total_amount)
        as total_sales,

    avg(total_amount)
        as average_transaction_value

from transactions

group by transaction_date

order by transaction_date