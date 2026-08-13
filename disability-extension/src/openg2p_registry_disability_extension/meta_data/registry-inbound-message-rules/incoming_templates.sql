INSERT INTO "public"."incoming_templates" ("template_id","register_id","data_model_id","template_document_id","jsonld_expansion_required","created_at","updated_at") VALUES
('926c9745-f820-4f4f-a25a-077c6558a903','a0000000-0000-4000-8000-000000000001','DM1','a1b2c3d4-0000-4000-8000-000000000002','FALSE','2026-04-01 00:00:00',NULL)
ON CONFLICT ("template_id") DO NOTHING;

-- DCI: dci_to_dr_person.json.j2
