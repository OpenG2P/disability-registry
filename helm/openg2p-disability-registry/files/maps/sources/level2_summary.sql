-- Aggregates one level deeper. Identical shape to level1_summary.sql; see that
-- file for why the columns are counts and why nothing is called `name`.
select
    p.geo_3_id                                                              as pcode,
    p.geo_3                                                                 as area_name,
    p.geo_2_id                                                              as parent_pcode,

    count(*)                                                                as registrants,
    count(*) filter (where p.has_unmet_support_need)                        as unmet_need,
    count(*) filter (where p.unmet_need_and_unenrolled)                     as unmet_and_unenrolled,
    count(*) filter (where p.currently_enrolled)                            as enrolled,
    count(*) filter (where p.disability_status_level in ('SEVERE', 'PROFOUND')) as severe_or_profound,
    count(*) filter (where p.certificate_expired)                           as certificate_expired,
    count(*) filter (where p.reassessment_overdue)                          as reassessment_overdue,
    count(*) filter (where p.age_band in ('0-4', '5-14'))                   as children,
    count(*) filter (where p.is_female)                                     as women_and_girls,

    round(100.0 * avg(case when p.has_unmet_support_need then 1 else 0 end), 1) as pct_unmet_need,
    round(100.0 * avg(case when p.currently_enrolled then 1 else 0 end), 1)     as pct_enrolled,
    round(avg(p.support_need_score)::numeric, 3)                            as avg_support_need_score
from dr_rpt_person p
where p.record_status = 'ACTIVE'
  and p.geo_3_id is not null
group by p.geo_3_id, p.geo_3, p.geo_2_id
order by unmet_need desc
