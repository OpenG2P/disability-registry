-- Aggregates for the Maps surface at the first level below country.
--
-- Named by DEPTH, not by level name. The reporting views unpack geography
-- positionally into geo_2/geo_2_id, so this query is identical for every
-- country; naming the file region/zone/province instead would bake one
-- country's hierarchy into a surface that is supposed to work for any pack.
--
-- `pcode` joins to level1.geojson. Nothing is called `name`: Evidence's map
-- input proxy is a callable and a `name` field collides with Function.name,
-- which kills the map outright.
select
    p.geo_2_id                                                              as pcode,
    p.geo_2                                                                 as area_name,

    -- COUNTS, not rates, for the headline figures. A rate needs a denominator
    -- big enough to survive one person moving; a count is exact whether the unit
    -- holds 17 registrants or 17,000, needs no suppression, and sums up the
    -- hierarchy. It is also the form an administrator can act on: "84 people
    -- with an unmet support need, none enrolled" is a work order, "12.4%
    -- covered" is not.
    count(*)                                                                as registrants,
    count(*) filter (where p.has_unmet_support_need)                        as unmet_need,
    count(*) filter (where p.unmet_need_and_unenrolled)                     as unmet_and_unenrolled,
    count(*) filter (where p.currently_enrolled)                            as enrolled,
    count(*) filter (where p.disability_status_level in ('SEVERE', 'PROFOUND')) as severe_or_profound,
    count(*) filter (where p.certificate_expired)                           as certificate_expired,
    count(*) filter (where p.reassessment_overdue)                          as reassessment_overdue,

    -- Children are the group most often missed by disability registration, so
    -- their count is carried separately rather than left to a filter.
    count(*) filter (where p.age_band in ('0-4', '5-14'))                   as children,
    count(*) filter (where p.is_female)                                     as women_and_girls,

    -- Rates for the map's colour scale. Safe here because the denominator is
    -- this unit's own registrant count, which the count column above shows
    -- alongside — so a percentage computed over eleven people is visibly that.
    round(100.0 * avg(case when p.has_unmet_support_need then 1 else 0 end), 1) as pct_unmet_need,
    round(100.0 * avg(case when p.currently_enrolled then 1 else 0 end), 1)     as pct_enrolled,
    round(avg(p.support_need_score)::numeric, 3)                            as avg_support_need_score
from dr_rpt_person p
where p.record_status = 'ACTIVE'
  and p.geo_2_id is not null
group by p.geo_2_id, p.geo_2
order by unmet_need desc
