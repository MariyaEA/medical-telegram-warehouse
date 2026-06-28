select *
from {{ ref('fct_messages') }}
where view_count < 0 or forward_count < 0
