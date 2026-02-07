
with cities_seed as (
    select * from {{ ref('cities') }}
),

distinct_stage_cities as (
    select distinct city_name from {{ ref('stg_weather') }}
)

select
    c.city_id,
    c.city_name,
    c.country,
    c.latitude,
    c.longitude
from cities_seed c
join distinct_stage_cities s on c.city_name = s.city_name
