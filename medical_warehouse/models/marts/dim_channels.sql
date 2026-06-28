with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

aggregated as (
    select
        md5(channel_slug) as channel_key,
        channel_slug,
        channel_name,
        case
            when channel_slug like '%lobelia%' then 'Cosmetics'
            when channel_slug like '%tikvah%' then 'Pharmaceutical'
            when channel_slug like '%chemed%' then 'Medical'
            else 'Medical'
        end as channel_type,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*) as total_posts,
        avg(view_count)::numeric(12,2) as avg_views
    from messages
    group by channel_slug, channel_name
)

select * from aggregated
