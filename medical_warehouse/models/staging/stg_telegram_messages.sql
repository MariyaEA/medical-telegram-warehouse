with source as (
    select *
    from raw.telegram_messages
),

cleaned as (
    select
        cast(message_id as bigint) as message_id,
        lower(trim(channel_username)) as channel_slug,
        trim(channel_name) as channel_name,
        cast(message_date as timestamp) as message_timestamp,
        cast(message_date as date) as message_date,
        nullif(trim(message_text), '') as message_text,
        coalesce(cast(views as integer), 0) as view_count,
        coalesce(cast(forwards as integer), 0) as forward_count,
        coalesce(cast(has_media as boolean), false) as has_media,
        case when image_path is not null then true else false end as has_image,
        media_type,
        image_path,
        length(coalesce(message_text, '')) as message_length,
        source_file,
        loaded_at
    from source
    where message_id is not null
      and channel_name is not null
      and message_date is not null
)

select * from cleaned
