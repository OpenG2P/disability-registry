-- Registry identity. The logo is left empty and set through the staff portal:
-- carrying a multi-megabyte base64 image in seed SQL makes every upgrade
-- rewrite it and makes this file unreviewable.
INSERT INTO "public"."g2p_registry_configuration" ("configuration_id","registry_name","registry_logo","registry_theme_id","registry_language_id") VALUES
('d49c0fae-777e-49b2-be3d-b0f1608d19bb','Disability Registry','','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','ccbcb97b-c4df-415d-9e4d-ec4985cf04e9')
ON CONFLICT ("configuration_id") DO NOTHING;
