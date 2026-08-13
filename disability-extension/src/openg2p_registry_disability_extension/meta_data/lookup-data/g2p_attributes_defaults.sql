-- Default values for this registry's code lists — GENERATED, do not hand-edit.
--
-- Regenerate with ./scripts/generate-code-lists.py after changing
-- register_domain/models/enums.py. test/test_enum_values.py fails the build if
-- this file and the enums disagree.
--
-- These are DEFAULTS, not a definition: load_attributes_from_mds replaces any
-- list the country pack also defines, and an admin can edit them in the staff
-- portal. A deployment with no country pack gets exactly these.

INSERT INTO "public"."g2p_attributes" ("attribute_id","attribute_code","attribute_display","is_hierarchical") VALUES 
('AGE_ONSET_BAND','AGE_ONSET_BAND','Age of Onset Band','FALSE'),
('ANIMAL_ASSISTANCE_TYPE','ANIMAL_ASSISTANCE_TYPE','Animal Assistance Type','FALSE'),
('ASSESSMENT_METHOD','ASSESSMENT_METHOD','Assessment Method','FALSE'),
('ASSISTIVE_TECHNOLOGY_TYPE','ASSISTIVE_TECHNOLOGY_TYPE','Assistive Technology Type','FALSE'),
('CAREGIVER_RELATIONSHIP','CAREGIVER_RELATIONSHIP','Caregiver Relationship','FALSE'),
('COMMUNICATION_NEED','COMMUNICATION_NEED','Communication Need','FALSE'),
('DISABILITY_STATUS','DISABILITY_STATUS','Disability Status','FALSE'),
('DISABILITY_STATUS_LEVEL','DISABILITY_STATUS_LEVEL','Disability Status Level','FALSE'),
('EDUCATION_LEVEL','EDUCATION_LEVEL','Education Level','FALSE'),
('EMPLOYMENT_STATUS','EMPLOYMENT_STATUS','Employment Status','FALSE'),
('GENDER','GENDER','Gender','FALSE'),
('HOUSING_SUPPORT_TYPE','HOUSING_SUPPORT_TYPE','Housing Support Type','FALSE'),
('HOUSING_TYPE','HOUSING_TYPE','Housing Type','FALSE'),
('HUMAN_ASSISTANCE_TYPE','HUMAN_ASSISTANCE_TYPE','Human Assistance Type','FALSE'),
('IDENTITY_EVIDENCE_TYPE','IDENTITY_EVIDENCE_TYPE','Identity Evidence Type','FALSE'),
('IMPAIRMENT_CAUSE','IMPAIRMENT_CAUSE','Impairment Cause','FALSE'),
('IMPAIRMENT_LEVEL','IMPAIRMENT_LEVEL','Impairment Level','FALSE'),
('IMPAIRMENT_TYPE','IMPAIRMENT_TYPE','Impairment Type','FALSE'),
('INCOME_LEVEL','INCOME_LEVEL','Income Level','FALSE'),
('LEGAL_CAPACITY_STATUS','LEGAL_CAPACITY_STATUS','Legal Capacity Status','FALSE'),
('MARITAL_STATUS','MARITAL_STATUS','Marital Status','FALSE'),
('MEDICAL_CARE_TYPE','MEDICAL_CARE_TYPE','Medical Care Type','FALSE'),
('PREFERRED_CONTACT_METHOD','PREFERRED_CONTACT_METHOD','Preferred Contact Method','FALSE'),
('PROGRAM_ENROLMENT_STATUS','PROGRAM_ENROLMENT_STATUS','Programme Enrolment Status','FALSE'),
('PROVISION_SOURCE','PROVISION_SOURCE','Provision Source','FALSE'),
('REGISTRATION_CHANNEL','REGISTRATION_CHANNEL','Registration Channel','FALSE'),
('RELATIONSHIP_TYPE','RELATIONSHIP_TYPE','Relationship Type','FALSE'),
('SUPPORT_FREQUENCY','SUPPORT_FREQUENCY','Support Frequency','FALSE'),
('SUPPORT_NEEDS_LEVEL','SUPPORT_NEEDS_LEVEL','Support Needs Level','FALSE'),
('SUPPORT_STATUS','SUPPORT_STATUS','Support Status','FALSE'),
('TRANSPORT_REQUIREMENT','TRANSPORT_REQUIREMENT','Transport Requirement','FALSE'),
('VERIFICATION_STATUS','VERIFICATION_STATUS','Verification Status','FALSE')
ON CONFLICT (attribute_id) DO NOTHING;
