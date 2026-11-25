-- Default values for this registry's code lists — GENERATED, do not hand-edit.
--
-- Regenerate with ./scripts/generate-code-lists.py after changing
-- register_domain/models/enums.py. test/test_metadata_consistency.py fails the
-- build if this file and the enums disagree.
--
-- These rows are for a Master Data that keeps lists in g2p_attributes /
-- g2p_attribute_values. The registry's own database has no such tables, so the
-- db-seed job cannot load them; scripts/load-code-lists.py does, and adds only
-- lists the Master Data does not already have. master-data/disability/ holds the
-- same lists in country-pack format.
--
-- These are DEFAULTS, not a definition: a list the country pack also defines is
-- the country's, and an admin can edit any of them in Master Data.

INSERT INTO "public"."g2p_attributes" ("attribute_id","attribute_code","attribute_display","is_hierarchical") VALUES 
('AGE_ONSET_BAND','AGE_ONSET_BAND','Age of onset band','FALSE'),
('ANIMAL_ASSISTANCE_TYPE','ANIMAL_ASSISTANCE_TYPE','Animal assistance type','FALSE'),
('ASSESSMENT_METHOD','ASSESSMENT_METHOD','Assessment method','FALSE'),
('ASSISTIVE_TECHNOLOGY_TYPE','ASSISTIVE_TECHNOLOGY_TYPE','Assistive technology type','FALSE'),
('CAREGIVER_RELATIONSHIP','CAREGIVER_RELATIONSHIP','Caregiver relationship','FALSE'),
('COMMUNICATION_NEED','COMMUNICATION_NEED','Communication need','FALSE'),
('DISABILITY_STATUS','DISABILITY_STATUS','Disability status','FALSE'),
('DISABILITY_STATUS_LEVEL','DISABILITY_STATUS_LEVEL','Disability status level','FALSE'),
('EDUCATION_LEVEL','EDUCATION_LEVEL','Education level','FALSE'),
('EMPLOYMENT_STATUS','EMPLOYMENT_STATUS','Employment status','FALSE'),
('GENDER','GENDER','Gender','FALSE'),
('HOUSING_SUPPORT_TYPE','HOUSING_SUPPORT_TYPE','Housing support type','FALSE'),
('HOUSING_TYPE','HOUSING_TYPE','Housing type','FALSE'),
('HUMAN_ASSISTANCE_TYPE','HUMAN_ASSISTANCE_TYPE','Human assistance type','FALSE'),
('IDENTITY_EVIDENCE_TYPE','IDENTITY_EVIDENCE_TYPE','Identity evidence type','FALSE'),
('IMPAIRMENT_CAUSE','IMPAIRMENT_CAUSE','Impairment cause','FALSE'),
('IMPAIRMENT_LEVEL','IMPAIRMENT_LEVEL','Impairment level','FALSE'),
('IMPAIRMENT_TYPE','IMPAIRMENT_TYPE','Impairment type','FALSE'),
('INCOME_LEVEL','INCOME_LEVEL','Income level','FALSE'),
('LEGAL_CAPACITY_STATUS','LEGAL_CAPACITY_STATUS','Legal capacity status','FALSE'),
('MARITAL_STATUS','MARITAL_STATUS','Marital status','FALSE'),
('MEDICAL_CARE_TYPE','MEDICAL_CARE_TYPE','Medical care type','FALSE'),
('PREFERRED_CONTACT_METHOD','PREFERRED_CONTACT_METHOD','Preferred contact method','FALSE'),
('PROGRAM_ENROLMENT_STATUS','PROGRAM_ENROLMENT_STATUS','Programme enrolment status','FALSE'),
('PROVISION_SOURCE','PROVISION_SOURCE','Provision source','FALSE'),
('REGISTRATION_CHANNEL','REGISTRATION_CHANNEL','Registration channel','FALSE'),
('RELATIONSHIP_TYPE','RELATIONSHIP_TYPE','Relationship type','FALSE'),
('SUPPORT_FREQUENCY','SUPPORT_FREQUENCY','Support frequency','FALSE'),
('SUPPORT_NEEDS_LEVEL','SUPPORT_NEEDS_LEVEL','Support needs level','FALSE'),
('SUPPORT_STATUS','SUPPORT_STATUS','Support status','FALSE'),
('TRANSPORT_REQUIREMENT','TRANSPORT_REQUIREMENT','Transport requirement','FALSE'),
('VERIFICATION_STATUS','VERIFICATION_STATUS','Verification status','FALSE')
ON CONFLICT (attribute_id) DO NOTHING;
