
with weather_data as (
    select * from {{ ref('stg_weather') }}
),

cities as (
    select * from {{ ref('dim_cities') }}
),

time_dim as (
    select * from {{ ref('dim_time') }}
)

select
    -- Surrogate key for the fact table
    md5(w.id || w.api_call_timestamp) as weather_id,
    
    -- Foreign Keys
    c.city_id,
    t.time_id,
    
    -- Measurements
    w.temperature,
    w.feels_like,
    w.humidity,
    w.pressure,
    w.wind_speed,
    w.wind_direction,
    w.precipitation,
    w.cloud_cover,
    w.uv_index,
    w.visibility,
    
    -- Descriptive attributes
    w.weather_description,
    
    -- Metadata
    w.ingestion_timestamp

from weather_data w
join cities c on w.city_name = c.city_name
join time_dim t on w.api_call_timestamp = t.timestamp
