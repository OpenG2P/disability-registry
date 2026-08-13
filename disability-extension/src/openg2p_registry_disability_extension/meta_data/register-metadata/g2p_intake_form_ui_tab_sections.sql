INSERT INTO "public"."g2p_intake_form_ui_tab_sections" ("tab_section_id","tab_id","section_id","section_order") VALUES 
('f1000000-0000-4000-8000-000000000001','dr_form_tab_pwd_intake','pwd_demographic_details',10),
('f1000000-0000-4000-8000-000000000002','dr_form_tab_pwd_intake','pwd_contact_details',20),
('f1000000-0000-4000-8000-000000000003','dr_form_tab_pwd_intake','pwd_identifier',30),
('f1000000-0000-4000-8000-000000000004','dr_form_tab_pwd_intake','pwd_location_details',40),
('f1000000-0000-4000-8000-000000000005','dr_form_tab_pwd_intake','pwd_disability_status',50),
('f1000000-0000-4000-8000-000000000006','dr_form_tab_pwd_intake','pwd_table_disability_details',60),
('f1000000-0000-4000-8000-000000000007','dr_form_tab_pwd_intake','pwd_living_situation',70),
('f1000000-0000-4000-8000-000000000008','dr_form_tab_pwd_intake','pwd_socio_economic',80),
('f1000000-0000-4000-8000-000000000009','dr_form_tab_pwd_intake','pwd_table_human_assistance',90),
('f1000000-0000-4000-8000-000000000010','dr_form_tab_pwd_intake','pwd_table_assistive_technology',100),
('f1000000-0000-4000-8000-000000000011','dr_form_tab_pwd_intake','pwd_table_medical_care',110),
('f1000000-0000-4000-8000-000000000012','dr_form_tab_pwd_intake','pwd_table_housing_support',120),
('f1000000-0000-4000-8000-000000000013','dr_form_tab_pwd_intake','pwd_table_animal_assistance',130),
('f1000000-0000-4000-8000-000000000014','dr_form_tab_pwd_intake','pwd_table_related_persons',140),
('f1000000-0000-4000-8000-000000000015','dr_form_tab_pwd_intake','pwd_table_program_enrolments',150)
ON CONFLICT ("tab_section_id") DO NOTHING;
