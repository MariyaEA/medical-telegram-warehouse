with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),
channels as (
    select channel_key, channel_slug from {{ ref('dim_channels') }}
),
dates as (
    select date_key, full_date from {{ ref('dim_dates') }}
)

select
    md5(messages.channel_slug || '-' || messages.message_id::text) as message_key,
    messages.message_id,
    channels.channel_key,
    dates.date_key,
    messages.message_timestamp,
    messages.message_text,
    messages.message_length,
    messages.view_count,
    messages.forward_count,
    messages.has_media,
    messages.has_image,
    messages.media_type,
    messages.image_path
from messages
left join channels on messages.channel_slug = channels.channel_slug
left join dates on messages.message_date = dates.full_date
