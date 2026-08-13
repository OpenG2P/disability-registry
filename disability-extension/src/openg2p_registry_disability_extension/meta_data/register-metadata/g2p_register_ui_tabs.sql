INSERT INTO "public"."g2p_register_ui_tabs" ("tab_id","register_id","tab_label","tab_order","is_active") VALUES 
('pwd_person_tab','a0000000-0000-4000-8000-000000000001','person_tab',1,'TRUE'),
('pwd_disability_tab','a0000000-0000-4000-8000-000000000001','disability_tab',2,'TRUE'),
('pwd_support_tab','a0000000-0000-4000-8000-000000000001','support_needs_tab',3,'TRUE'),
('pwd_inclusion_tab','a0000000-0000-4000-8000-000000000001','inclusion_and_living_tab',4,'TRUE'),
('pwd_network_tab','a0000000-0000-4000-8000-000000000001','related_persons_tab',5,'TRUE'),
('pwd_programs_tab','a0000000-0000-4000-8000-000000000001','programmes_tab',6,'TRUE')
ON CONFLICT ("tab_id") DO NOTHING;
