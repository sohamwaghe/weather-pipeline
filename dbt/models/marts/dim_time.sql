
with distinct_timestamps as (
    select distinct api_call_timestamp as timestamp_value
    from {{ ref('stg_weather') }}
)

select
    -- Surrogate key for time
    md5(cast(timestamp_value as varchar)) as time_id,
    timestamp_value as timestamp,
    
    -- Extract time attributes
    extract(hour from timestamp_value) as hour,
    extract(day from timestamp_value) as day,
    extract(month from timestamp_value) as month,
    extract(year from timestamp_value) as year,
    extract(dow from timestamp_value) as day_of_week,
    
    -- Boolean flags
    case 
        when extract(dow from timestamp_value) in (0, 6) then true 
        else false 
    end as is_weekend,
    
    -- Formatting
    to_char(timestamp_value, 'Month') as month_name,
    to_char(timestamp_value, 'Day') as day_name

from distinct_timestamps
