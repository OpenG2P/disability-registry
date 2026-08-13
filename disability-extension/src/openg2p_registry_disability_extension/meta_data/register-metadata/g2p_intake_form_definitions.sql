INSERT INTO "public"."g2p_intake_form_definitions" ("form_id","register_id","form_mnemonic","form_description","number_of_verifications","used_only_in_ingestion_pipeline") VALUES
('c1000000-0000-4000-8000-000000000001','a0000000-0000-4000-8000-000000000001','person_with_disability_intake_form','Captures identity, assessed disability status, impairment detail, living situation and support needs for a person with disability.',0,'FALSE')
ON CONFLICT ("form_id") DO NOTHING;
