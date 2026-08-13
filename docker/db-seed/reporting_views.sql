-- Disability Registry reporting layer
-- =============================================================================
-- Flattens the register into wide, indexed materialized views that the Superset
-- dashboards and the Insights maps surface both read. Charts then stay simple
-- SELECTs instead of repeating multi-table joins and JSONB digging.
--
-- Country-agnostic by construction
-- --------------------------------
-- Geography is unpacked from geo_code_hierarchy_json BY POSITION (ordinality),
-- never by level name. A deployment with country/region/district/ward/village
-- and one with region/zone/woreda/kebele both populate geo_1..geo_n in their own
-- order. Nothing here assumes a country, a naming scheme, or a fixed depth.
--
-- What this registry's reports are actually FOR
-- ---------------------------------------------
-- Two questions, and both are about the gap between need and provision:
--   1. how many people need support of a given kind and are not getting it, and
--   2. where those people are.
-- Every view below exists to answer one of those. That is why the support
-- sub-registers are unioned into a single `dr_rpt_support_need` view rather than
-- reported separately — "unmet need" is a question about all five at once, and
-- five separate views make every dashboard re-derive the union.
--
-- Refresh after a load (CONCURRENTLY needs the unique indexes at the bottom,
-- which in turn need one non-concurrent refresh — CREATE ... AS does that):
--
--   REFRESH MATERIALIZED VIEW CONCURRENTLY dr_rpt_person;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY dr_rpt_support_need;
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Persons with disability — one row per registrant
-- ---------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS dr_rpt_person CASCADE;
CREATE MATERIALIZED VIEW dr_rpt_person AS
WITH geo AS (
    SELECT
        p.internal_record_id AS person_id,
        MAX(CASE WHEN t.ordinality = 1 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_1,
        MAX(CASE WHEN t.ordinality = 2 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_2,
        MAX(CASE WHEN t.ordinality = 3 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_3,
        MAX(CASE WHEN t.ordinality = 4 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_4,
        MAX(CASE WHEN t.ordinality = 5 THEN t.elem ->> 'level_value_mnemonic' END) AS geo_5,
        MAX(CASE WHEN t.ordinality = 1 THEN t.elem ->> 'level_value_id' END) AS geo_1_id,
        MAX(CASE WHEN t.ordinality = 2 THEN t.elem ->> 'level_value_id' END) AS geo_2_id,
        MAX(CASE WHEN t.ordinality = 3 THEN t.elem ->> 'level_value_id' END) AS geo_3_id,
        MAX(CASE WHEN t.ordinality = 4 THEN t.elem ->> 'level_value_id' END) AS geo_4_id,
        MAX(CASE WHEN t.ordinality = 5 THEN t.elem ->> 'level_value_id' END) AS geo_5_id
    FROM g2p_register_persons_with_disability p,
         LATERAL jsonb_array_elements(p.geo_code_hierarchy_json -> 'hierarchy')
                 WITH ORDINALITY AS t(elem, ordinality)
    WHERE p.geo_code_hierarchy_json IS NOT NULL
    GROUP BY p.internal_record_id
),
primary_impairment AS (
    -- The impairment flagged primary, falling back to the most severe recorded.
    -- The fallback matters: is_primary_impairment is optional, and without it a
    -- third of the register would report a NULL impairment type.
    SELECT DISTINCT ON (link_internal_record_id)
           link_internal_record_id AS person_id,
           impairment_type,
           impairment_level,
           impairment_cause,
           age_on_set,
           age_onset_band
    FROM g2p_register_disability_details
    WHERE record_status = 'ACTIVE'
    ORDER BY link_internal_record_id,
             is_primary_impairment DESC NULLS LAST,
             CASE impairment_level
                 WHEN 'CANNOT_DO_AT_ALL'    THEN 4
                 WHEN 'A_LOT_OF_DIFFICULTY' THEN 3
                 WHEN 'SOME_DIFFICULTY'     THEN 2
                 WHEN 'NO_DIFFICULTY'       THEN 1
                 ELSE 0
             END DESC
),
impairment_counts AS (
    SELECT link_internal_record_id AS person_id,
           count(*)                                          AS impairment_count,
           bool_or(impairment_type = 'MULTIPLE') OR count(*) > 1 AS has_multiple_impairments,
           string_agg(DISTINCT impairment_type, ', ' ORDER BY impairment_type) AS impairment_types
    FROM g2p_register_disability_details
    WHERE record_status = 'ACTIVE'
    GROUP BY link_internal_record_id
),
prog AS (
    -- Collapsed to one row per person so the join below cannot fan out and
    -- double-count people.
    SELECT link_internal_record_id AS person_id,
           bool_or(enrolment_status IN ('ACTIVE', 'ENROLLED')) AS currently_enrolled,
           count(*)                                            AS programme_count,
           min(enrolment_start_date)                           AS first_enrolled_on,
           string_agg(DISTINCT program_name, ', ' ORDER BY program_name) AS programmes
    FROM g2p_register_program_enrolments
    WHERE record_status = 'ACTIVE'
    GROUP BY link_internal_record_id
),
caregivers AS (
    SELECT link_internal_record_id AS person_id,
           count(*) FILTER (WHERE is_primary_caregiver)          AS primary_caregiver_count,
           bool_or(is_legal_guardian)                            AS has_legal_guardian,
           bool_or(is_co_resident)                               AS has_co_resident_relative
    FROM g2p_register_related_persons
    WHERE record_status = 'ACTIVE'
    GROUP BY link_internal_record_id
),
score AS (
    SELECT DISTINCT ON (link_internal_record_id)
           link_internal_record_id AS person_id,
           computed_score,
           score_type,
           computed_at
    FROM g2p_register_scores
    ORDER BY link_internal_record_id, computed_at DESC
)
SELECT
    p.internal_record_id                        AS person_id,
    p.functional_record_id,
    p.created_at,
    p.record_status,
    p.registration_date,
    p.registration_channel,

    -- Demographics. Names and identifiers are deliberately EXCLUDED: this view
    -- feeds dashboards and a shared maps surface, and disability status is
    -- special-category data under most data-protection regimes. Aggregate
    -- reporting needs the attributes, never the person.
    p.gender,
    (p.gender = 'FEMALE')                       AS is_female,
    p.birth_date,
    CASE
        WHEN p.birth_date IS NULL THEN 'UNKNOWN'
        WHEN date_part('year', age(p.birth_date)) < 5  THEN '0-4'
        WHEN date_part('year', age(p.birth_date)) < 15 THEN '5-14'
        WHEN date_part('year', age(p.birth_date)) < 25 THEN '15-24'
        WHEN date_part('year', age(p.birth_date)) < 40 THEN '25-39'
        WHEN date_part('year', age(p.birth_date)) < 60 THEN '40-59'
        ELSE '60+'
    END                                         AS age_band,
    (p.death_date IS NOT NULL)                  AS is_deceased,

    -- Disability status and assessment
    p.self_id_disability,
    p.disability_status,
    p.disability_status_level,
    p.support_needs_level,
    p.assessment_date,
    p.certificate_expiry_date,
    (p.certificate_expiry_date IS NOT NULL
     AND p.certificate_expiry_date < CURRENT_DATE) AS certificate_expired,
    p.next_reassessment_date,
    (p.next_reassessment_date IS NOT NULL
     AND p.next_reassessment_date < CURRENT_DATE)  AS reassessment_overdue,

    -- Impairment
    pi.impairment_type                          AS primary_impairment_type,
    pi.impairment_level                         AS primary_impairment_level,
    pi.impairment_cause                         AS primary_impairment_cause,
    pi.age_on_set                               AS primary_age_on_set,
    pi.age_onset_band                           AS primary_age_onset_band,
    COALESCE(ic.impairment_count, 0)            AS impairment_count,
    COALESCE(ic.has_multiple_impairments, FALSE) AS has_multiple_impairments,
    ic.impairment_types,

    -- Living situation and inclusion
    p.housing_type,
    p.transport_requirement,
    p.lives_alone,
    p.legal_capacity_status,
    p.guardian_required,
    p.employment_status,
    (p.employment_status IN ('EMPLOYED', 'SELF_EMPLOYED',
                             'SHELTERED_EMPLOYMENT', 'SUPPORTED_EMPLOYMENT')) AS is_in_work,
    p.education_level,

    -- Support summary. Denormalised on the register (see the domain service);
    -- carried through here so the headline chart is a single-table scan.
    COALESCE(p.unmet_support_needs_count, 0)    AS unmet_support_needs_count,
    COALESCE(p.has_unmet_support_need, FALSE)   AS has_unmet_support_need,

    -- Care network
    COALESCE(cg.primary_caregiver_count, 0)     AS primary_caregiver_count,
    COALESCE(cg.has_legal_guardian, FALSE)      AS has_legal_guardian,
    COALESCE(cg.has_co_resident_relative, FALSE) AS has_co_resident_relative,

    -- Programmes
    COALESCE(pr.currently_enrolled, FALSE)      AS currently_enrolled,
    COALESCE(pr.programme_count, 0)             AS programme_count,
    pr.first_enrolled_on,
    pr.programmes,
    -- The coverage gap this registry exists to expose.
    (COALESCE(p.has_unmet_support_need, FALSE)
     AND NOT COALESCE(pr.currently_enrolled, FALSE)) AS unmet_need_and_unenrolled,

    -- Score
    s.computed_score                            AS support_need_score,
    s.score_type                                AS support_need_score_type,
    s.computed_at                               AS support_need_scored_at,

    -- Geography
    g.geo_1, g.geo_2, g.geo_3, g.geo_4, g.geo_5,
    g.geo_1_id, g.geo_2_id, g.geo_3_id, g.geo_4_id, g.geo_5_id
FROM g2p_register_persons_with_disability p
LEFT JOIN geo                 g  ON g.person_id  = p.internal_record_id
LEFT JOIN primary_impairment  pi ON pi.person_id = p.internal_record_id
LEFT JOIN impairment_counts   ic ON ic.person_id = p.internal_record_id
LEFT JOIN prog                pr ON pr.person_id = p.internal_record_id
LEFT JOIN caregivers          cg ON cg.person_id = p.internal_record_id
LEFT JOIN score               s  ON s.person_id  = p.internal_record_id;

CREATE UNIQUE INDEX IF NOT EXISTS dr_rpt_person_pk        ON dr_rpt_person (person_id);
CREATE INDEX        IF NOT EXISTS dr_rpt_person_geo       ON dr_rpt_person (geo_1, geo_2, geo_3);
CREATE INDEX        IF NOT EXISTS dr_rpt_person_status    ON dr_rpt_person (disability_status, disability_status_level);
CREATE INDEX        IF NOT EXISTS dr_rpt_person_unmet     ON dr_rpt_person (has_unmet_support_need);
CREATE INDEX        IF NOT EXISTS dr_rpt_person_impair    ON dr_rpt_person (primary_impairment_type);

-- ---------------------------------------------------------------------------
-- Support needs — the five DO.DR.05 sub-registers as one long table
-- ---------------------------------------------------------------------------
-- One row per (person, support kind, support item). `support_domain` says which
-- sub-register it came from, so a single chart can compare unmet need across
-- assistive technology, medical care, housing, human assistance and animal
-- assistance without five separate queries and five chances to define "unmet"
-- differently.
DROP MATERIALIZED VIEW IF EXISTS dr_rpt_support_need CASCADE;
CREATE MATERIALIZED VIEW dr_rpt_support_need AS
WITH unioned AS (
    SELECT internal_record_id, link_internal_record_id, record_status,
           'HUMAN_ASSISTANCE'::text AS support_domain,
           assistance_type::text    AS support_type,
           support_status::text     AS support_status,
           registration_date
    FROM g2p_register_human_assistances
    UNION ALL
    SELECT internal_record_id, link_internal_record_id, record_status,
           'ASSISTIVE_TECHNOLOGY', assistive_technology_type::text,
           support_status::text, registration_date
    FROM g2p_register_assistive_technologies
    UNION ALL
    SELECT internal_record_id, link_internal_record_id, record_status,
           'MEDICAL_CARE', medical_care_type::text,
           support_status::text, registration_date
    FROM g2p_register_medical_cares
    UNION ALL
    SELECT internal_record_id, link_internal_record_id, record_status,
           'HOUSING_SUPPORT', housing_support_type::text,
           support_status::text, registration_date
    FROM g2p_register_housing_supports
    UNION ALL
    SELECT internal_record_id, link_internal_record_id, record_status,
           'ANIMAL_ASSISTANCE', animal_assistance_type::text,
           support_status::text, registration_date
    FROM g2p_register_animal_assistances
)
SELECT
    u.internal_record_id                        AS support_id,
    u.link_internal_record_id                   AS person_id,
    u.record_status,
    u.support_domain,
    u.support_type,
    u.support_status,
    u.registration_date,
    -- The single definition of "unmet" for the whole reporting layer. Must match
    -- UNMET_STATUSES in the domain service and in load_sample_data.py.
    (u.support_status IN ('REQUIRED', 'PARTIALLY_RECEIVED')) AS is_unmet,
    (u.support_status IN ('RECEIVING', 'RECEIVED'))          AS is_met,

    -- Person attributes carried down, so "unmet need by sex" or "by age band"
    -- is a single-table group-by rather than a join in every chart.
    p.gender,
    p.is_female,
    p.age_band,
    p.disability_status_level,
    p.support_needs_level,
    p.primary_impairment_type,
    p.currently_enrolled,
    p.geo_1, p.geo_2, p.geo_3, p.geo_4, p.geo_5,
    p.geo_1_id, p.geo_2_id, p.geo_3_id, p.geo_4_id, p.geo_5_id
FROM unioned u
JOIN dr_rpt_person p ON p.person_id = u.link_internal_record_id
WHERE u.record_status = 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS dr_rpt_support_need_pk     ON dr_rpt_support_need (support_id);
CREATE INDEX        IF NOT EXISTS dr_rpt_support_need_person ON dr_rpt_support_need (person_id);
CREATE INDEX        IF NOT EXISTS dr_rpt_support_need_geo    ON dr_rpt_support_need (geo_1, geo_2, geo_3);
CREATE INDEX        IF NOT EXISTS dr_rpt_support_need_domain ON dr_rpt_support_need (support_domain, support_status);
CREATE INDEX        IF NOT EXISTS dr_rpt_support_need_unmet  ON dr_rpt_support_need (is_unmet);
