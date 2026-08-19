-- Theme palette.
--
-- The users of this registry are government staff — registration officers,
-- assessment boards, caseworkers — not the people whose records it holds. The
-- contrast ratios below are still deliberate: these are screens somebody reads
-- all day, and many public-sector bodies are bound by an accessibility standard
-- for their internal systems. #1F4E79 on #FFFFFF is 8.6:1; #B34700 on #FFFFFF
-- is 4.9:1, both past WCAG 2.1 AA (4.5:1 for body text). Replace them in a
-- country pack by all means — but check the replacement rather than assuming
-- brand colours pass.
--
-- font_url / font_family are left empty so the platform default applies;
-- dashboard_image is set through the staff portal rather than carried as a
-- multi-megabyte base64 blob in seed SQL.
INSERT INTO "public"."registry_theme_values" ("theme_value_id","theme_id","attribute_name","attribute_value") VALUES
('c1a00000-0000-4000-8000-000000000001','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','primary_color_1','#1F4E79'),
('c1a00000-0000-4000-8000-000000000002','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','primary_color_2','#B34700'),
('c1a00000-0000-4000-8000-000000000003','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','secondary_color_1','#F2F6FA'),
('c1a00000-0000-4000-8000-000000000004','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','secondary_color_2','#E1E1E1'),
('c1a00000-0000-4000-8000-000000000005','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','secondary_color_3','#767676'),
('c1a00000-0000-4000-8000-000000000006','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','neutral_color_1','#000000'),
('c1a00000-0000-4000-8000-000000000007','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','neutral_color_2','#FFFFFF'),
('c1a00000-0000-4000-8000-000000000008','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','font_url',''),
('c1a00000-0000-4000-8000-000000000009','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','font_family',''),
('c1a00000-0000-4000-8000-00000000000a','b7e41d55-018f-4ee4-bff5-b0e95a993ea2','dashboard_image','')
ON CONFLICT ("theme_value_id") DO NOTHING;
