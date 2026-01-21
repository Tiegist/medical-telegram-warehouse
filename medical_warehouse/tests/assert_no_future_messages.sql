select *
from {{ ref('fct_messages') }}
where message_date > now()


