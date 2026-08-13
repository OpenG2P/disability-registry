-- SUPPORT_NEED is a triage score, not an eligibility gate. See
-- score_compute/services/support_need.py for what that distinction means and
-- why the score is rescaled by total weight.
INSERT INTO "public"."g2p_register_score_definitions" (
    "score_definition_id",
    "register_mnemonic",
    "score_type",
    "is_enabled"
) VALUES (
    'e0000000-0000-4000-8000-000000000001',
    'PersonWithDisability',
    'SUPPORT_NEED',
    'TRUE'
)
ON CONFLICT ("score_definition_id") DO NOTHING;
