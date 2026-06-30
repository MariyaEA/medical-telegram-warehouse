with detections as (
    select * from {{ ref('stg_yolo_detections') }}
),
messages as (
    select
        message_id,
        channel_key,
        date_key
    from {{ ref('fct_messages') }}
)
select
    md5(cast(detections.message_id as text) || '-' || detections.detected_class || '-' || cast(detections.confidence_score as text)) as image_detection_key,
    detections.message_id,
    messages.channel_key,
    messages.date_key,
    detections.image_path,
    detections.detected_class,
    detections.confidence_score,
    detections.image_category
from detections
left join messages
    on detections.message_id = messages.message_id
