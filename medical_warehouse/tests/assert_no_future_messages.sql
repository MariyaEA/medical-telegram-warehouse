select *
from {{ ref('fct_messages') }}
where message_timestamp::date > current_date
