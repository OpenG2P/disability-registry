-- Which enricher + intake form handles an inbound message.
--
-- SP1 creates a new person via the intake form (so the record goes through the
-- normal approval path rather than appearing in the register unreviewed).
-- SP2 updates an existing person directly, targeting the demographic section.
INSERT INTO "public"."incoming_model_semantic_patterns" ("semantic_pattern_id","data_model_id","register_id","intake_form_id","pattern_for_register","pattern_for_intake_form","key_path_for_business_payload","raw_payload_enricher_class","section_id","pattern_for_section") VALUES
('SP1','DM1','a0000000-0000-4000-8000-000000000001','c1000000-0000-4000-8000-000000000001','$.body.message.search_response[0].data.reg_type=>^ns:org:RegistryType:Disability$','$.body.message.search_response[0].data.reg_record_type=>^PersonwithDisability$','$.body.message.search_response[0].data.reg_records[0]','G2PDciPersonWithDisabilityCreateEnricherService','',''),
('SP2','DM1','a0000000-0000-4000-8000-000000000001','','$.body.message.search_response[0].data.reg_type=>^ns:org:RegistryType:Disability$','','$.body.message.search_response[0].data.reg_records[0]','G2PDciPersonWithDisabilityUpdateEnricherService','pwd_demographic_details','$.body.message.search_response[0].data.reg_record_type=>^spdci-extensions-dci:Person$')
ON CONFLICT ("semantic_pattern_id") DO NOTHING;
