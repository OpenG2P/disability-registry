-- Curated code lists — hand-maintained, unlike the *_defaults.sql files.
--
-- These have no enum behind them because their members are institutions and
-- programmes rather than domain concepts: they differ in every deployment and
-- must be replaceable by a country pack without a code change.
INSERT INTO "public"."g2p_attributes" ("attribute_id","attribute_code","attribute_display","is_hierarchical") VALUES
('PROGRAM_NAME','PROGRAM_NAME','Programme Name','FALSE'),
('ASSESSMENT_AUTHORITY','ASSESSMENT_AUTHORITY','Assessment Authority','FALSE'),
('DATA_SOURCE','DATA_SOURCE','Data Source','FALSE')
ON CONFLICT (attribute_id) DO NOTHING;
