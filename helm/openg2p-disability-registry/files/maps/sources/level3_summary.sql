-- Aggregates at the third level below country — usually the lowest level with
-- a published boundary file. See level1_summary.sql for the column rationale.
--
-- Rates are omitted here on purpose. At this depth a unit often holds only a
-- handful of registrants, and a percentage over six people is not a statistic —
-- it is one person's record, rounded. Counts remain exact and need no
-- suppression, which is why the map colours this level by count.
select
    p.geo_4_id                                                              as pcode,
    p.geo_4                                                                 as area_name,
    p.geo_3_id                                                              as parent_pcode,

    count(*)                                                                as registrants,
    count(*) filter (where p.has_unmet_support_need)                        as unmet_need,
    count(*) filter (where p.unmet_need_and_unenrolled)                     as unmet_and_unenrolled,
    count(*) filter (where p.currently_enrolled)                            as enrolled,
    count(*) filter (where p.disability_status_level in ('SEVERE', 'PROFOUND')) as severe_or_profound,
    count(*) filter (where p.certificate_expired)                           as certificate_expired,
    count(*) filter (where p.age_band in ('0-4', '5-14'))                   as children,
    count(*) filter (where p.is_female)                                     as women_and_girls
from dr_rpt_person p
where p.record_status = 'ACTIVE'
  and p.geo_4_id is not null
group by p.geo_4_id, p.geo_4, p.geo_3_id
order by unmet_need desc
