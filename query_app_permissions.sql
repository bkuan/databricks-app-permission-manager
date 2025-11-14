SELECT
event_id,
  event_date,
  event_time,
  workspace_id,
  user_identity.email AS user,
  request_params.request_object_id AS app,
  request_params.access_control_list
FROM system.access.audit
WHERE action_name LIKE "changeAppsAcl"
ORDER BY event_time DESC;