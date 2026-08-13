INSERT INTO "public"."g2p_input_mechanisms" ("mechanism_id","register_id","mechanism_type","display_key") VALUES
('1','a0000000-0000-4000-8000-000000000001','INTAKE_FORM','Intake Form')
ON CONFLICT ("mechanism_id") DO NOTHING;
