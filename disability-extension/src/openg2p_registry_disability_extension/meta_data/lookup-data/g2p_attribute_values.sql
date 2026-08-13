-- Values for the curated code lists.
--
-- Generic disability-programme archetypes, chosen so the registry is usable
-- out of the box in any country and replaced wholesale by a country pack. The
-- value_id values match ProgramEnum in register_domain/models/enums.py.
INSERT INTO "public"."g2p_attribute_values" ("value_id","attribute_id","value_code","value_display","parent_value_id","sort_order") VALUES
('PROG_DISABILITY_ALLOWANCE','PROGRAM_NAME','DISABILITY_ALLOWANCE','Disability Allowance',NULL,1),
('PROG_CAREGIVER_ALLOWANCE','PROGRAM_NAME','CAREGIVER_ALLOWANCE','Caregiver Allowance',NULL,2),
('PROG_ASSISTIVE_DEVICE_GRANT','PROGRAM_NAME','ASSISTIVE_DEVICE_GRANT','Assistive Device Grant',NULL,3),
('PROG_HEALTH_INSURANCE','PROGRAM_NAME','HEALTH_INSURANCE','Health Insurance Scheme',NULL,4),
('PROG_REHABILITATION_SERVICES','PROGRAM_NAME','REHABILITATION_SERVICES','Rehabilitation Services',NULL,5),
('PROG_INCLUSIVE_EDUCATION','PROGRAM_NAME','INCLUSIVE_EDUCATION','Inclusive Education Support',NULL,6),
('PROG_VOCATIONAL_TRAINING','PROGRAM_NAME','VOCATIONAL_TRAINING','Vocational Training',NULL,7),
('PROG_EMPLOYMENT_QUOTA','PROGRAM_NAME','EMPLOYMENT_QUOTA','Employment Quota Scheme',NULL,8),
('PROG_HOUSING_ADAPTATION','PROGRAM_NAME','HOUSING_ADAPTATION','Housing Adaptation Grant',NULL,9),
('PROG_TRANSPORT_CONCESSION','PROGRAM_NAME','TRANSPORT_CONCESSION','Transport Concession',NULL,10),
('AA_MEDICAL_BOARD','ASSESSMENT_AUTHORITY','MEDICAL_BOARD','District Medical Board',NULL,1),
('AA_HOSPITAL','ASSESSMENT_AUTHORITY','HOSPITAL','Designated Hospital',NULL,2),
('AA_REHABILITATION_CENTRE','ASSESSMENT_AUTHORITY','REHABILITATION_CENTRE','Rehabilitation Centre',NULL,3),
('AA_SOCIAL_WELFARE_OFFICE','ASSESSMENT_AUTHORITY','SOCIAL_WELFARE_OFFICE','Social Welfare Office',NULL,4),
('AA_MOBILE_ASSESSMENT_TEAM','ASSESSMENT_AUTHORITY','MOBILE_ASSESSMENT_TEAM','Mobile Assessment Team',NULL,5),
('DS_SELF_REPORT','DATA_SOURCE','SELF_REPORT','Self-report',NULL,1),
('DS_CLINICAL_ASSESSMENT','DATA_SOURCE','CLINICAL_ASSESSMENT','Clinical assessment',NULL,2),
('DS_FIELD_VERIFICATION','DATA_SOURCE','FIELD_VERIFICATION','Field verification',NULL,3),
('DS_PROGRAMME_MIS','DATA_SOURCE','PROGRAMME_MIS','Programme MIS integration',NULL,4),
('DS_FOUNDATIONAL_ID','DATA_SOURCE','FOUNDATIONAL_ID','Foundational ID API',NULL,5),
('DS_SOCIAL_REGISTRY','DATA_SOURCE','SOCIAL_REGISTRY','Social registry transfer',NULL,6),
('DS_CRVS','DATA_SOURCE','CRVS','Civil registration (CRVS)',NULL,7),
('DS_OPD_REFERRAL','DATA_SOURCE','OPD_REFERRAL','Organisation of persons with disabilities',NULL,8)
ON CONFLICT (value_id) DO NOTHING;
