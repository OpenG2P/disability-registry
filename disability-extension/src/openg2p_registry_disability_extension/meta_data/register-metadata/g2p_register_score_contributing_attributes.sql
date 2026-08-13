-- Contributors to the SUPPORT_NEED score.
--
-- Weights sum to 1.0 here, but the compute service rescales by the total anyway,
-- so a deployment can add or remove a contributor without invalidating every
-- previously computed score.
--
-- `unmet_support_needs_count` carries the most weight deliberately: an unmet
-- need is an observed service gap, whereas severity is a clinical judgement that
-- says nothing about whether the person is already supported.
INSERT INTO "public"."g2p_register_score_contributing_attributes" (
    "contributing_attribute_id",
    "register_mnemonic",
    "score_type",
    "attribute_name",
    "attribute_computation_required",
    "attribute_computation_value",
    "attribute_weightage"
) VALUES
(
    'e0000000-0000-4000-8000-000000000011',
    'PersonWithDisability',
    'SUPPORT_NEED',
    'unmet_support_needs_count',
    'FALSE',
    NULL,
    0.40
),
(
    'e0000000-0000-4000-8000-000000000012',
    'PersonWithDisability',
    'SUPPORT_NEED',
    'support_needs_level',
    'FALSE',
    NULL,
    0.35
),
(
    'e0000000-0000-4000-8000-000000000013',
    'PersonWithDisability',
    'SUPPORT_NEED',
    'disability_status_level',
    'FALSE',
    NULL,
    0.25
)
ON CONFLICT ("contributing_attribute_id") DO NOTHING;
