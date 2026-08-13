-- Unmet support need broken down by SUPPORT DOMAIN, one row per area per domain.
--
-- This is the query the maps surface exists for. "Where is the need?" is
-- answered by level2_summary; "need for WHAT?" can only be answered here,
-- because the answer determines which agency acts — assistive technology is a
-- procurement problem, housing support is a public-works problem, and human
-- assistance is a caregiver-allowance problem.
--
-- Reads dr_rpt_support_need, which is the union of the five DO.DR.05
-- sub-registers with one shared definition of `is_unmet`.
select
    s.geo_3_id                                          as pcode,
    s.geo_3                                             as area_name,
    s.geo_2_id                                          as parent_pcode,
    s.support_domain,

    count(*)                                            as support_records,
    count(*) filter (where s.is_unmet)                  as unmet,
    count(*) filter (where s.is_met)                    as met,
    count(distinct s.person_id) filter (where s.is_unmet) as people_with_unmet_need,

    -- The most-requested item in this area and domain: what to procure first.
    mode() within group (order by s.support_type)
      filter (where s.is_unmet)                         as top_unmet_type
from dr_rpt_support_need s
where s.geo_3_id is not null
group by s.geo_3_id, s.geo_3, s.geo_2_id, s.support_domain
order by unmet desc
