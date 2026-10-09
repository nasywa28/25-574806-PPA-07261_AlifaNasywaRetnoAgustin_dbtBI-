with source_data as (

    select *
    from {{ source('raw', 'transaksi') }}

),

renamed_and_typed as (

    select
        cast(transaction_id as varchar) as transaction_id,

        cast(transaction_date as date) as transaction_date,

        cast(product_name as varchar) as product_name,

        cast(category as varchar) as category,

        cast(quantity as integer) as quantity,

        cast(unit_price as double) as unit_price,

        cast(customer_city as varchar) as customer_city,

        cast(quantity as integer)
            * cast(unit_price as double) as total_amount

    from source_data

),

cleaned as (

    select *

    from renamed_and_typed

    where transaction_id is not null
      and transaction_date is not null
      and product_name is not null
      and quantity > 0
      and unit_price >= 0

),

deduplicated as (

    select
        *,

        row_number() over (
            partition by transaction_id
            order by transaction_date
        ) as duplicate_number

    from cleaned

)

select
    transaction_id,
    transaction_date,
    product_name,
    category,
    quantity,
    unit_price,
    customer_city,
    total_amount

from deduplicated

where duplicate_number = 1