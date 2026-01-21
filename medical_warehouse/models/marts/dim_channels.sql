with base as (
    select * from {{ ref('stg_telegram_messages') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['channel_name']) }} as channel_key,
    channel_name,
    case
        when lower(channel_name) like '%cosmetic%' or lower(channel_name) like '%lobelia%' then 'Cosmetics'
        when lower(channel_name) like '%pharma%' or lower(channel_name) like '%pharmacy%' or lower(channel_name) like '%tikvah%' then 'Pharmaceutical'
        else 'Medical'
    end as channel_type,
    min(message_date) as first_post_date,
    max(message_date) as last_post_date,
    count(*) as total_posts,
    avg(view_count) as avg_views
from base
group by channel_name


