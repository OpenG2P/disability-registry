-- Binds this registry's register and intake form to the AWE approval policies
-- seeded by awe_meta_data/.
--
-- Only the master register is bound. Sub-register rows are edited as part of a
-- change request against the person, so they inherit that request's approval;
-- binding them separately would demand a second approval for the same edit.
INSERT INTO "public"."g2p_registry_awe_policy_configurations" (
    "awe_policy_config_id",
    "policy_scope",
    "register_id",
    "intake_form_id",
    "section_id",
    "policy_type",
    "policy_key",
    "context_field_names"
) VALUES
    ('a2000000-0000-4000-8000-000000000001', 'REGISTER', 'a0000000-0000-4000-8000-000000000001', '', '', 'registry.change_request', 'registry.change_request.person_with_disability', 'null'),
    ('a2000000-0000-4000-8000-000000000011', 'INTAKE_FORM', 'a0000000-0000-4000-8000-000000000001', 'c1000000-0000-4000-8000-000000000001', '', 'registry.intake_form', 'registry.intake_form.person_with_disability', 'null')
ON CONFLICT ("awe_policy_config_id") DO NOTHING;
