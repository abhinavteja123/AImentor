
2026-01-31 19:59:12,174 - sqlalchemy.engine.Engine - INFO - BEGIN (implicit)

2026-01-31 19:59:12,174 - sqlalchemy.engine.Engine - INFO - SELECT users.id, users.email, users.password_hash, users.full_name, users.is_active, users.is_verified, users.created_at, users.last_login 

FROM users 

WHERE users.id = $1::UUID

2026-01-31 19:59:12,174 - sqlalchemy.engine.Engine - INFO - [cached since 24.22s ago] (UUID('918de996-2192-4aae-9123-d9ea74fb127a'),)

2026-01-31 19:59:12,176 - sqlalchemy.engine.Engine - INFO - SELECT roadmaps.id, roadmaps.user_id, roadmaps.title, roadmaps.description, roadmaps.target_role, roadmaps.total_weeks, roadmaps.start_date, roadmaps.end_date, roadmaps.completion_percentage, roadmaps.status, roadmaps.milestones, roadmaps.generation_params, roadmaps.created_at, roadmaps.updated_at 

FROM roadmaps 

WHERE roadmaps.id = $1::UUID AND roadmaps.user_id = $2::UUID

2026-01-31 19:59:12,176 - sqlalchemy.engine.Engine - INFO - [cached since 12.17s ago] (UUID('ca0d749d-51c2-4070-83cc-1a856f1a0250'), UUID('918de996-2192-4aae-9123-d9ea74fb127a'))

2026-01-31 19:59:12,177 - sqlalchemy.engine.Engine - INFO - SELECT roadmap_tasks.roadmap_id AS roadmap_tasks_roadmap_id, roadmap_tasks.id AS roadmap_tasks_id, roadmap_tasks.week_number AS roadmap_tasks_week_number, roadmap_tasks.day_number AS roadmap_tasks_day_number, roadmap_tasks.order_in_day AS roadmap_tasks_order_in_day, roadmap_tasks.task_title AS roadmap_tasks_task_title, roadmap_tasks.task_description AS roadmap_tasks_task_description, roadmap_tasks.task_type AS roadmap_tasks_task_type, roadmap_tasks.estimated_duration AS roadmap_tasks_estimated_duration, roadmap_tasks.difficulty AS roadmap_tasks_difficulty, roadmap_tasks.learning_objectives AS roadmap_tasks_learning_objectives, roadmap_tasks.success_criteria AS roadmap_tasks_success_criteria, roadmap_tasks.prerequisites AS roadmap_tasks_prerequisites, roadmap_tasks.resources AS roadmap_tasks_resources, roadmap_tasks.status AS roadmap_tasks_status, roadmap_tasks.completed_at AS roadmap_tasks_completed_at, roadmap_tasks.skipped_reason AS roadmap_tasks_skipped_reason, roadmap_tasks.notes AS roadmap_tasks_notes, roadmap_tasks.is_favorite AS roadmap_tasks_is_favorite, roadmap_tasks.created_at AS roadmap_tasks_created_at, roadmap_tasks.updated_at AS roadmap_tasks_updated_at 

FROM roadmap_tasks 

WHERE roadmap_tasks.roadmap_id IN ($1::UUID)

2026-01-31 19:59:12,177 - sqlalchemy.engine.Engine - INFO - [cached since 15.04s ago] (UUID('ca0d749d-51c2-4070-83cc-1a856f1a0250'),)

2026-01-31 19:59:12,179 - sqlalchemy.engine.Engine - INFO - SELECT roadmap_tasks.id, roadmap_tasks.roadmap_id, roadmap_tasks.week_number, roadmap_tasks.day_number, roadmap_tasks.order_in_day, roadmap_tasks.task_title, roadmap_tasks.task_description, roadmap_tasks.task_type, roadmap_tasks.estimated_duration, roadmap_tasks.difficulty, roadmap_tasks.learning_objectives, roadmap_tasks.success_criteria, roadmap_tasks.prerequisites, roadmap_tasks.resources, roadmap_tasks.status, roadmap_tasks.completed_at, roadmap_tasks.skipped_reason, roadmap_tasks.notes, roadmap_tasks.is_favorite, roadmap_tasks.created_at, roadmap_tasks.updated_at 

FROM roadmap_tasks 

WHERE roadmap_tasks.roadmap_id = $1::UUID AND roadmap_tasks.week_number = $2::INTEGER ORDER BY roadmap_tasks.day_number, roadmap_tasks.order_in_day

2026-01-31 19:59:12,179 - sqlalchemy.engine.Engine - INFO - [cached since 12.16s ago] (UUID('ca0d749d-51c2-4070-83cc-1a856f1a0250'), 1)

2026-01-31 19:59:12,180 - sqlalchemy.engine.Engine - INFO - COMMIT
