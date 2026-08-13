-- DEMO approvers, matching the demo users the platform's keycloak-init creates.
-- A real deployment replaces these with role-based rules for its own officials;
-- see Phase 3, which lists rotating these among the pre-handover steps.
INSERT INTO "public"."approver_rule" (
    "id",
    "stage_id",
    "rule_type",
    "rule_value",
    "kind",
    "required",
    "created_at",
    "updated_at"
)
SELECT v."id", v."stage_id", v."rule_type", v."rule_value"::json, v."kind",
       v."required"::boolean, v."created_at"::timestamptz, v."updated_at"::timestamptz
FROM (VALUES
    ('d1000000-0000-4000-8000-0000000000d1', 'b1000000-0000-4000-8000-0000000000d1', 'user', '{"user_id": "alex.carter"}', 'approver', 'FALSE', NOW(), NOW()),
    ('d1000000-0000-4000-8000-0000000000d2', 'b1000000-0000-4000-8000-0000000000d2', 'user', '{"user_id": "nina.patel"}', 'approver', 'FALSE', NOW(), NOW()),
    ('d1000000-0000-4000-8000-0000000000d3', 'b1000000-0000-4000-8000-0000000000d3', 'user', '{"user_id": "alex.carter"}', 'approver', 'FALSE', NOW(), NOW()),
    ('d1000000-0000-4000-8000-0000000000d4', 'b1000000-0000-4000-8000-0000000000d4', 'user', '{"user_id": "nina.patel"}', 'approver', 'FALSE', NOW(), NOW())
) AS v("id","stage_id","rule_type","rule_value","kind","required","created_at","updated_at")
-- Same reason as the stage filter: a rule whose stage was skipped must not abort
-- the statement and take the valid rules with it.
WHERE EXISTS (SELECT 1 FROM "public"."approval_stage" s WHERE s.id = v."stage_id")
ON CONFLICT DO NOTHING;
