INSERT INTO "public"."g2p_intake_form_ui_tabs" ("tab_id","form_id","tab_label","tab_order") VALUES 
('dr_form_tab_pwd_intake','c1000000-0000-4000-8000-000000000001','person_with_disability_intake_form',1)
ON CONFLICT ("tab_id") DO NOTHING;
