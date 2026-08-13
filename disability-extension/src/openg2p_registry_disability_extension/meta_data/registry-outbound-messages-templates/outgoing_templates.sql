INSERT INTO "public"."outgoing_templates" ("template_id","data_model_id","register_id","template_document_id","created_at","updated_at") VALUES
('b752f09f-ea02-4355-b37b-3a6c95b7354d','DM1','a0000000-0000-4000-8000-000000000001','a1b2c3d4-0000-4000-8000-000000000001','2026-04-01 00:00:00',NULL)
ON CONFLICT ("template_id") DO NOTHING;

-- DCI: dr_person_to_dci.json.j2
-- The TOP-LEVEL keys of that template are this registry's consent scopes.
