INSERT INTO "public"."data_models" ("data_model_id","data_model_mnemonic","pattern_for_data_model","response_template_document_id","is_active") VALUES
('DM1','DCI','*','56619678-0cad-4eb1-924e-6e74fb20291f','TRUE')
ON CONFLICT ("data_model_id") DO NOTHING;

-- DCI response template: dci_commons_response.json.j2
