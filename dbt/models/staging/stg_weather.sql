
with raw_data as (
    select * from {{ source('raw', 'weather_data') }}
),

staged_weather as (
    select
        id,
        city_name,
        
        -- Timestamp casting
        api_call_timestamp::timestamp as api_call_timestamp,
        ingestion_timestamp::timestamp as ingestion_timestamp,
        
        -- Extraction from WeatherStack JSON structure
        -- JSON operators: 
        -- -> gets JSON object field
        -- ->> gets JSON object field as text
        (api_response->'current'->>'temperature')::float as temperature, 
        (api_response->'current'->>'feelslike')::float as feels_like,
        
        -- WeatherStack gives temp in Celsius by default (metric units)
        -- No conversion needed unlike Kelvin from OWM
        
        (api_response->'current'->>'humidity')::integer as humidity,
        (api_response->'current'->>'pressure')::integer as pressure,
        (api_response->'current'->>'wind_speed')::float as wind_speed,
        (api_response->'current'->>'wind_dir')::varchar as wind_direction,
        (api_response->'current'->>'precip')::float as precipitation,
        (api_response->'current'->>'cloudcover')::integer as cloud_cover,
        (api_response->'current'->>'uv_index')::integer as uv_index,
        (api_response->'current'->>'visibility')::integer as visibility,
        
        -- Weather descriptions is an array, we take the first element
        -- operator #>> '{key, index}' accesses nested path as text
        (api_response #>> '{current,weather_descriptions,0}')::varchar as weather_description,
        
        -- Location metadata
        (api_response->'location'->>'country')::varchar as country,
        (api_response->'location'->>'region')::varchar as region,
        (api_response->'location'->>'lat')::float as latitude,
        (api_response->'location'->>'lon')::float as longitude

    from raw_data
)

select * from staged_weather
