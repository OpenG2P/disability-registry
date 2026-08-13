-- Disability Registry — register definitions.
--
-- ONE top-level register (PersonWithDisability, purpose REGISTER) and eight
-- detail tables hanging off it. There is deliberately no group/household
-- register: this registry's subject is the individual, and the relationships
-- that matter are carried by RelatedPerson rather than by co-residence.
--
-- `master_register_id` on the detail rows is what makes them appear as child
-- records of the person; `register_rank` orders them in the staff portal.
-- register_id values are FROZEN — every section, tab, template and AWE policy
-- references them by literal UUID.
INSERT INTO "public"."g2p_register_definitions" ("register_id","register_mnemonic","register_subject","register_description","master_register_id","register_rank","functional_id_generation_required","register_purpose","program_id","program_mnemonic","register_icon","has_image","dedup_is_enabled","dedup_threshold_score","completion_score_required","outgest_applicable","requires_registrant_authentication","registrant_authentication_validity_days","registrant_re_auth_warning_days_before") VALUES
('a0000000-0000-4000-8000-000000000001','PersonWithDisability','Persons with Disability','Master register of persons with disability — identity, assessed disability status, living situation and support needs (SPDCI DO.DR.01 / DO.DR.02 / DO.DR.03)',NULL,1,'TRUE','REGISTER',NULL,NULL,'','TRUE','TRUE',0.75,'FALSE','TRUE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000010','DisabilityDetail','Disability Details','Per-impairment detail — type, level, cause and age of onset (SPDCI DO.DR.04). One row per impairment; co-occurring impairments are the norm','a0000000-0000-4000-8000-000000000001',10,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000020','HumanAssistance','Human Assistance','Care and personal assistance required or received, with caregiver details (SPDCI DO.DR.06)','a0000000-0000-4000-8000-000000000001',20,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000030','AssistiveTechnology','Assistive Technology','Assistive products required or received, from the WHO Priority Assistive Products List (SPDCI DO.DR.07)','a0000000-0000-4000-8000-000000000001',30,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000040','MedicalCare','Medical Care','Chronic medical care required or received, and its out-of-pocket cost (SPDCI DO.DR.08)','a0000000-0000-4000-8000-000000000001',40,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000050','HousingSupport','Housing Support','Support addressing barriers in housing — adaptations, relocation, subsidised or supported accommodation (SPDCI DO.DR.09)','a0000000-0000-4000-8000-000000000001',50,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000060','AnimalAssistance','Animal Assistance','Assistance animals required or received (SPDCI DO.DR.10)','a0000000-0000-4000-8000-000000000001',60,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000070','RelatedPerson','Related Persons','Family, guardians, caregivers and emergency contacts (SPDCI DO.DR.02 related_person)','a0000000-0000-4000-8000-000000000001',70,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('b0000000-0000-4000-8000-000000000080','ProgramEnrolment','Programme Enrolments','Other social protection programmes the person benefits from (SPDCI DO.DR.03 programs_enrolments)','a0000000-0000-4000-8000-000000000001',80,'FALSE','TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30),
('c0000000-0000-4000-8000-000000000001','Score','Scores','Latest computed scores (`g2p_register_scores`; `score_type` SUPPORT_NEED)','a0000000-0000-4000-8000-000000000001',90,'FALSE','CORE_TABLE',NULL,NULL,NULL,'FALSE','FALSE',0,'FALSE','FALSE','FALSE',730,30)
ON CONFLICT ("register_id") DO NOTHING;
