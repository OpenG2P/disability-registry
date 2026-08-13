INSERT INTO "public"."approval_policy" (
    "id",
    "policy_key",
    "version",
    "name",
    "description",
    "status",
    "artifact_type",
    "created_by",
    "forbid_self_approval",
    "forbid_repeat_approvers",
    "created_at",
    "updated_at"
) VALUES
    ('a1000000-0000-4000-8000-0000000000d1', 'registry.change_request.person_with_disability', 1, 'Policy for Person with Disability Change Request', 'Two-stage review of edits to a person with disability record.', 'active', 'registry.change_request', 'seed', 'TRUE', 'TRUE', NOW(), NOW()),
    ('a1000000-0000-4000-8000-0000000000d2', 'registry.intake_form.person_with_disability', 1, 'Policy for Person with Disability Intake Form', 'Two-stage review of a new registration.', 'active', 'registry.intake_form', 'seed', 'TRUE', 'TRUE', NOW(), NOW())
-- forbid_self_approval / forbid_repeat_approvers are TRUE here, unlike the
-- reference registry's permissive defaults. Disability status determines
-- entitlement, so a single official must not be able to both record and approve
-- it — that is the standard control against fraudulent certification.
--
-- Untargeted DO NOTHING, not ON CONFLICT ("id"): `approval_policy` also carries
-- uq_policy_key_version. AWE is shared across registries, so another registry can
-- already own the same policy_key under a DIFFERENT id; targeting "id" leaves that
-- natural-key clash unguarded and the whole multi-row statement aborts, landing
-- none of the policies. Untargeted skips only the offending row.
ON CONFLICT DO NOTHING;
