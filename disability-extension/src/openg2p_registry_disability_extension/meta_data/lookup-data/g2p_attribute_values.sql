-- Values for the curated code lists.
--
-- Generic disability-programme archetypes, chosen so the registry is usable
-- out of the box in any country and replaced wholesale by a country pack.
--
-- value_id equals value_code, as in every list a country pack carries: the
-- staff portal stores value_code, and the sample data uses these same codes.
-- (ProgramEnum in register_domain/models/enums.py still spells the programmes
-- with a PROG_ prefix; the program_name column is a free string and is not
-- checked against it.)
--
-- Like the *_defaults.sql files these rows are for Master Data, not for the
-- registry's own database: see scripts/load-code-lists.py.
INSERT INTO "public"."g2p_attribute_values" ("value_id","attribute_id","value_code","value_display","parent_value_id","sort_order") VALUES
('DISABILITY_ALLOWANCE','PROGRAM_NAME','DISABILITY_ALLOWANCE','Disability Allowance',NULL,1),
('CAREGIVER_ALLOWANCE','PROGRAM_NAME','CAREGIVER_ALLOWANCE','Caregiver Allowance',NULL,2),
('ASSISTIVE_DEVICE_GRANT','PROGRAM_NAME','ASSISTIVE_DEVICE_GRANT','Assistive Device Grant',NULL,3),
('HEALTH_INSURANCE','PROGRAM_NAME','HEALTH_INSURANCE','Health Insurance Scheme',NULL,4),
('REHABILITATION_SERVICES','PROGRAM_NAME','REHABILITATION_SERVICES','Rehabilitation Services',NULL,5),
('INCLUSIVE_EDUCATION','PROGRAM_NAME','INCLUSIVE_EDUCATION','Inclusive Education Support',NULL,6),
('VOCATIONAL_TRAINING','PROGRAM_NAME','VOCATIONAL_TRAINING','Vocational Training',NULL,7),
('EMPLOYMENT_QUOTA','PROGRAM_NAME','EMPLOYMENT_QUOTA','Employment Quota Scheme',NULL,8),
('HOUSING_ADAPTATION','PROGRAM_NAME','HOUSING_ADAPTATION','Housing Adaptation Grant',NULL,9),
('TRANSPORT_CONCESSION','PROGRAM_NAME','TRANSPORT_CONCESSION','Transport Concession',NULL,10),
('MEDICAL_BOARD','ASSESSMENT_AUTHORITY','MEDICAL_BOARD','District Medical Board',NULL,1),
('HOSPITAL','ASSESSMENT_AUTHORITY','HOSPITAL','Designated Hospital',NULL,2),
('REHABILITATION_CENTRE','ASSESSMENT_AUTHORITY','REHABILITATION_CENTRE','Rehabilitation Centre',NULL,3),
('SOCIAL_WELFARE_OFFICE','ASSESSMENT_AUTHORITY','SOCIAL_WELFARE_OFFICE','Social Welfare Office',NULL,4),
('MOBILE_ASSESSMENT_TEAM','ASSESSMENT_AUTHORITY','MOBILE_ASSESSMENT_TEAM','Mobile Assessment Team',NULL,5),
('SELF_REPORT','DATA_SOURCE','SELF_REPORT','Self-report',NULL,1),
('CLINICAL_ASSESSMENT','DATA_SOURCE','CLINICAL_ASSESSMENT','Clinical assessment',NULL,2),
('FIELD_VERIFICATION','DATA_SOURCE','FIELD_VERIFICATION','Field verification',NULL,3),
('PROGRAMME_MIS','DATA_SOURCE','PROGRAMME_MIS','Programme MIS integration',NULL,4),
('FOUNDATIONAL_ID','DATA_SOURCE','FOUNDATIONAL_ID','Foundational ID API',NULL,5),
('SOCIAL_REGISTRY','DATA_SOURCE','SOCIAL_REGISTRY','Social registry transfer',NULL,6),
('CRVS','DATA_SOURCE','CRVS','Civil registration (CRVS)',NULL,7),
('OPD_REFERRAL','DATA_SOURCE','OPD_REFERRAL','Organisation of persons with disabilities',NULL,8)
ON CONFLICT DO NOTHING;
