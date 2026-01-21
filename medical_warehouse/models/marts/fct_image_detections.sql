with detections as (
    select
        message_id::bigint as message_id,
        channel_name,
        detected_class,
        confidence_score::float as confidence_score,
        image_category
    from {{ source('raw', 'yolo_detections') }}
)
select
    d.message_id,
    m.channel_key,
    m.date_key,
    d.detected_class,
    d.confidence_score,
    d.image_category
from detections d
left join {{ ref('fct_messages') }} m on m.message_id = d.message_id


