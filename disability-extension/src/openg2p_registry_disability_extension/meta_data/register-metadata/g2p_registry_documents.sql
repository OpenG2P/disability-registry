-- Jinja templates, uploaded to MinIO by db-seed when dbSeed.loadTemplates=true.
-- document_id values are referenced by incoming_templates / outgoing_templates /
-- data_models, so they are frozen.
INSERT INTO "public"."g2p_registry_documents" ("document_id","document_store_id","bucket","source_filename","created_by","created_at") VALUES
('56619678-0cad-4eb1-924e-6e74fb20291f','dci_commons_response.json.j2','templates','dci_commons_response.json.j2','seeder','2026-04-01 00:00:00'),
('a1b2c3d4-0000-4000-8000-000000000001','dr_person_to_dci.json.j2','templates','dr_person_to_dci.json.j2','seeder','2026-04-01 00:00:00'),
('a1b2c3d4-0000-4000-8000-000000000002','dci_to_dr_person.json.j2','templates','dci_to_dr_person.json.j2','seeder','2026-04-01 00:00:00')
ON CONFLICT ("document_id") DO NOTHING;
