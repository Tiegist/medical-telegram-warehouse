with source as (
    select * from {{ source('raw', 'telegram_messages') }}
),
cleaned as (
    select
        message_id::bigint as message_id,
        channel_name,
        message_date::timestamp as message_date,
        coalesce(message_text, '') as message_text,
        has_media::boolean as has_media,
        nullif(image_path, '') as image_path,
        coalesce(views, 0)::int as view_count,
        coalesce(forwards, 0)::int as forward_count,
        length(coalesce(message_text, '')) as message_length,
        case when nullif(image_path, '') is not null then true else false end as has_image
    from source
    where message_id is not null
)
select * from cleaned


