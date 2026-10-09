with transactions as (

    select *
    from {{ ref('stg_transaksi') }}

)

select
    product_name,
    category,

    count(distinct transaction_id)
        as total_transactions,

    sum(quantity)
        as total_quantity,

    sum(total_amount)
        as total_sales,

    avg(total_amount)
        as average_transaction_value

from transactions

group by
    product_name,
    category

order by total_sales desc