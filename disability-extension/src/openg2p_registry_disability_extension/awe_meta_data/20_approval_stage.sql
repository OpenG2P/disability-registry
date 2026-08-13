INSERT INTO "public"."approval_stage" (
    "id",
    "policy_id",
    "stage_order",
    "name",
    "mode",
    "mode_value",
    "sla_hours",
    "parallel_group",
    "skip_if",
    "on_empty",
    "on_breach",
    "escalation_rules_json",
    "created_at",
    "updated_at"
)
SELECT v."id", v."policy_id", v."stage_order"::int, v."name", v."mode",
       v."mode_value"::int, v."sla_hours"::int, v."parallel_group"::int,
       v."skip_if"::json, v."on_empty", v."on_breach",
       v."escalation_rules_json"::json, v."created_at"::timestamptz, v."updated_at"::timestamptz
FROM (VALUES
    ('b1000000-0000-4000-8000-0000000000d1', 'a1000000-0000-4000-8000-0000000000d1', 1, 'Case Officer Review', 'all', NULL, 72, NULL, 'null', 'block', NULL, 'null', NOW(), NOW()),
    ('b1000000-0000-4000-8000-0000000000d2', 'a1000000-0000-4000-8000-0000000000d1', 2, 'Disability Assessment Officer Approval', 'all', NULL, 120, NULL, 'null', 'block', NULL, 'null', NOW(), NOW()),
    ('b1000000-0000-4000-8000-0000000000d3', 'a1000000-0000-4000-8000-0000000000d2', 1, 'Case Officer Review', 'all', NULL, 72, NULL, 'null', 'block', NULL, 'null', NOW(), NOW()),
    ('b1000000-0000-4000-8000-0000000000d4', 'a1000000-0000-4000-8000-0000000000d2', 2, 'Disability Assessment Officer Approval', 'all', NULL, 120, NULL, 'null', 'block', NULL, 'null', NOW(), NOW())
) AS v("id","policy_id","stage_order","name","mode","mode_value","sla_hours",
        "parallel_group","skip_if","on_empty","on_breach","escalation_rules_json",
        "created_at","updated_at")
-- Skip stages whose policy is absent: a policy row can legitimately be skipped
-- above (another registry already owns that policy_key), and without this filter
-- the orphan's FK violation aborts the statement, taking valid stages with it.
WHERE EXISTS (SELECT 1 FROM "public"."approval_policy" p WHERE p.id = v."policy_id")
ON CONFLICT DO NOTHING;
