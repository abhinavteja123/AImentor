26-01-31 21:18:07,136 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)

2026-01-31 21:18:07,137 - sqlalchemy.engine.Engine - INFO - SELECT users.id, users.email, users.password_hash, users.full_name, users.is_active, users.is_verified, users.created_at, users.last_login 

FROM users 

WHERE users.id = $1::UUID

2026-01-31 21:18:07,137 - sqlalchemy.engine.Engine - INFO - [cached since 97.99s ago] (UUID('918de996-2192-4aae-9123-d9ea74fb127a'),)

2026-01-31 21:18:07,139 - sqlalchemy.engine.Engine - INFO - ROLLBACK

2026-01-31 21:18:07,136 INFO sqlalchemy.engine.Engine BEGIN (implicit)

2026-01-31 21:18:07,137 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.password_hash, users.full_name, users.is_active, users.is_verified, users.created_at, users.last_login 

FROM users 

WHERE users.id = $1::UUID

2026-01-31 21:18:07,137 INFO sqlalchemy.engine.Engine [cached since 97.99s ago] (UUID('918de996-2192-4aae-9123-d9ea74fb127a'),)

2026-01-31 21:18:07,139 INFO sqlalchemy.engine.Engine ROLLBACK

INFO:     172.20.0.1:46704 - "PUT /api/v1/resume/update HTTP/1.1" 422 Unprocessable Entity