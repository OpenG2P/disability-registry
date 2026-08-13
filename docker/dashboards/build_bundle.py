#!/usr/bin/env python3
"""Build the default Disability Registry Superset dashboard bundle.

Produces the importable ZIP the Helm chart carries:

    python build_bundle.py --out ../../helm/openg2p-disability-registry/files/dr-dashboards.zip
    superset import-dashboards -p dr-dashboards.zip -u admin

The ZIP is NOT committed. It is a binary nobody can review or diff, and a
checked-in bundle drifts away from the reporting views it reads without anyone
noticing. Build it as part of preparing a release; `analytics.dashboards.enabled`
defaults to false so an install without one simply skips the import.

Design notes
------------
* **Deterministic UUIDs.** Every asset's uuid is uuid5(namespace, stable key),
  so re-importing the same bundle UPDATES the existing assets instead of
  creating duplicates. That is what makes this safe to run on every install and
  upgrade rather than once.

* **Portable viz types only.** The bundle has to import into Superset 4.0.1
  (currently deployed) and 6.1 (where we are heading). Only viz types verified
  present in both are used — big_number_total, pie, echarts_timeseries_bar,
  table. Notably `dist_bar` is avoided: it exists in 4.0.1 but was removed with
  the NVD3 plugin in 6.x, so a chart using it saves fine and then renders blank.

* **Adhoc metrics, not metric names.** A bare string in a chart's metric field
  is resolved against the dataset's SAVED metrics, of which a fresh dataset has
  exactly one (`count`). Anything else has to be expressed as an adhoc metric or
  the chart 400s at query time.

* **Charts read the reporting views**, not the register tables — see
  ../db-seed/reporting_views.sql. Geography is exposed as positional columns
  geo_1..geo_5, so no chart hardcodes a country's level names.

* **The dashboards are about the GAP, not the population.** A disability
  registry that reports how many people it holds is reporting on itself. Every
  dashboard here is built around unmet need, coverage and the exclusions that
  keep people out — because those are the numbers somebody can act on.
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone

import yaml

# Fixed namespace for uuid5. Do not change it: the derived asset UUIDs are what
# let a re-import update the existing dashboards instead of duplicating them.
NS = uuid.UUID("9c2e7b41-5d0a-4e83-b6f1-2a7c4e9d8b30")
BUNDLE = "dr_dashboards"
DB_NAME = "DR"
SCHEMA = "public"

# The two hand-written reporting views. P is one row per registrant; S is the
# union of the five DO.DR.05 support sub-registers, one row per support record.
P = "dr_rpt_person"
S = "dr_rpt_support_need"


def uid(*parts) -> str:
    return str(uuid.uuid5(NS, "/".join(parts)))


def slug(name: str, limit: int = 60) -> str:
    """Filename-safe slug that always starts with an alphanumeric.

    A chart called "% with foundational ID" otherwise yields
    "__with_foundational_ID.yaml", and the importer skips files whose names
    start with an underscore — the chart vanishes from the bundle silently,
    with no error and a dashboard that is simply missing a tile.
    """
    s = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    return (s or "chart")[:limit]


# ---------------------------------------------------------------------------
# metric / column helpers
# ---------------------------------------------------------------------------
def simple(col, agg, label):
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": col},
        "aggregate": agg,
        "label": label,
        "hasCustomLabel": True,
    }


def sql_metric(expr, label):
    """Adhoc SQL metric — used for the percentage-of-a-boolean measures that
    make up most social protection indicators (coverage, prevalence, gaps)."""
    return {
        "expressionType": "SQL",
        "sqlExpression": expr,
        "label": label,
        "hasCustomLabel": True,
    }


# d3 format for a ratio: multiplies by 100 and appends the sign, so 0.124 -> 12.4%.
PCT_FORMAT = ".1%"


def pct(col, label):
    """Share of rows where a boolean column is true, as a RATIO (0-1).

    Returns a ratio rather than an already-multiplied percentage so the chart
    can format it with d3's "%" — which multiplies by 100 and appends the sign.
    Emitting 12.4 and formatting it as SMART_NUMBER, as this used to, printed a
    bare "12.4" with nothing to say it was a percentage. Multiplying here AND
    formatting as a percent would print "1240%".

    The private __pct__ marker tells the chart helpers to apply PCT_FORMAT; they
    pop it before the metric is serialised, so Superset never sees it.
    """
    m = sql_metric(f"AVG(CASE WHEN {col} THEN 1.0 ELSE 0 END)", label)
    m["__pct__"] = True
    return m


def pct_expr(expr, label):
    """A ratio metric from an arbitrary expression, marked like pct().

    For the conditional shares — coverage of the poorest quintile, leakage to
    the richest — where the denominator is a subset rather than every row.
    """
    m = sql_metric(expr, label)
    m["__pct__"] = True
    return m


def _fmt_for(metrics):
    """PCT_FORMAT when every metric here is a ratio from pct(), else the default.

    Mixed charts keep SMART_NUMBER: a percent format applied to a count would
    multiply it by 100.
    """
    ms = metrics if isinstance(metrics, list) else [metrics]
    flags = [bool(m.pop("__pct__", False)) if isinstance(m, dict) else False for m in ms]
    return PCT_FORMAT if flags and all(flags) else "SMART_NUMBER"


# Columns where NULL means "the question does not apply" and the reporting view
# therefore labels the value NA. Shown as the chart's description so a reader who
# meets an NA slice can find out what it means without leaving the dashboard.
NA_MEANING = {
    "disability_status": "NA = no assessment recorded yet.",
    "disability_status_level": "NA = not assessed, or assessed as not disabled.",
    "support_needs_level": "NA = support needs not yet classified.",
    "primary_impairment_type": "NA = registered but no impairment detail recorded — a data-completeness gap, not an absence of impairment.",
    "primary_impairment_cause": "NA = cause not recorded or not known.",
    "primary_age_onset_band": "NA = age of onset not recorded.",
    "employment_status": "NA = not of working age.",
    "education_level": "NA = too young for school, or not recorded.",
    "housing_type": "NA = living situation not recorded.",
    "transport_requirement": "NA = transport needs not assessed.",
    "legal_capacity_status": "NA = legal capacity not reviewed.",
    "support_domain": "One of the five SPDCI support objects: human assistance, assistive technology, medical care, housing support, animal assistance.",
}


def na_note(*dims):
    """The NA explanation for whichever of these dimensions can carry one."""
    seen, out = set(), []
    for d in dims:
        for col in (d if isinstance(d, list) else [d]):
            if isinstance(col, str) and col in NA_MEANING and col not in seen:
                seen.add(col)
                out.append(NA_MEANING[col])
    return " ".join(out) or None


# COUNT(*) as an adhoc SQL metric, NOT simple("*", "COUNT", ...). A SIMPLE
# adhoc metric names a column, and Superset validates that name against the
# dataset's real columns — "*" is not one, so every chart using it fails at
# render with "Columns missing in dataset: ['*']" even though the underlying
# SQL is perfectly valid.
COUNT = sql_metric("COUNT(*)", "Total")


# ---------------------------------------------------------------------------
# chart definitions
# ---------------------------------------------------------------------------
def big(name, dataset, metric, subheader=""):
    return {
        "name": name, "dataset": dataset, "viz_type": "big_number_total",
        "params": {"metric": metric, "subheader": subheader,
                   "y_axis_format": _fmt_for(metric)},
    }


def bar(name, dataset, x, metrics, series=None, row_limit=100, sort_desc=True):
    p = {
        "x_axis": x, "metrics": metrics, "groupby": series or [],
        "row_limit": row_limit, "orientation": "vertical",
        "x_axis_sort_asc": not sort_desc, "sort_series_type": "sum",
        "y_axis_format": _fmt_for(metrics), "rich_tooltip": True,
    }
    return {"name": name, "dataset": dataset, "viz_type": "echarts_timeseries_bar",
            "params": p, "description": na_note(x, series)}


def pie(name, dataset, groupby, metric, row_limit=25):
    return {
        "name": name, "dataset": dataset, "viz_type": "pie",
        "params": {"groupby": groupby, "metric": metric, "row_limit": row_limit,
                   "donut": True, "show_labels": True, "label_type": "key_percent",
                   "number_format": _fmt_for(metric)},
        "description": na_note(groupby),
    }


def table(name, dataset, groupby, metrics, row_limit=100):
    """A table mixes counts and ratios, so the format goes per COLUMN.

    Capture the ratio labels before _fmt_for runs — it pops the __pct__ marker,
    which must not reach Superset. Forgetting that call here was a real bug: the
    marker leaked into six exported charts, because every other helper popped it
    and this one did not.
    """
    pct_labels = [m["label"] for m in metrics
                  if isinstance(m, dict) and m.get("__pct__")]
    _fmt_for(metrics)
    return {
        "name": name, "dataset": dataset, "viz_type": "table",
        "description": na_note(groupby),
        "params": {"query_mode": "aggregate", "groupby": groupby, "metrics": metrics,
                   "row_limit": row_limit, "include_search": True,
                   "order_desc": True, "server_pagination": False,
                   "column_config": {lbl: {"d3NumberFormat": PCT_FORMAT}
                                     for lbl in pct_labels}},
    }


def build_charts():
    """Every chart, grouped by the dashboard it belongs to.

    Ordered as a caseworker's questions are: who is registered, what do they
    need, are they getting it, who is being missed, and is the register itself
    still true.
    """
    d = {}

    # -- 1. Unmet support need ----------------------------------------------
    # The headline dashboard. Everything here is a gap, not a total.
    d["Unmet Support Need"] = [
        big("People with an unmet need", P, sql_metric(
            "COUNT(CASE WHEN has_unmet_support_need THEN 1 END)", "People")),
        big("Share with an unmet need", P, pct("has_unmet_support_need", "% unmet")),
        big("Unmet need, no programme", P, sql_metric(
            "COUNT(CASE WHEN unmet_need_and_unenrolled THEN 1 END)", "People")),
        big("Average unmet needs per person", P,
            simple("unmet_support_needs_count", "AVG", "Avg unmet needs")),
        # Which KIND of support is missing decides which agency acts, so this is
        # the first cut rather than a detail.
        bar("Unmet support records by domain", S, "support_domain",
            [sql_metric("COUNT(CASE WHEN is_unmet THEN 1 END)", "Unmet")]),
        pie("Support status across all domains", S, ["support_status"], COUNT),
        bar("Unmet need by area", P, "geo_2", [sql_metric(
            "COUNT(CASE WHEN has_unmet_support_need THEN 1 END)", "People with unmet need")]),
        table("Most requested unmet support", S, ["support_domain", "support_type"],
              [sql_metric("COUNT(CASE WHEN is_unmet THEN 1 END)", "Unmet"),
               sql_metric("COUNT(CASE WHEN is_met THEN 1 END)", "Met"),
               pct("is_unmet", "% of records unmet")]),
    ]

    # -- 2. Support provision by domain --------------------------------------
    d["Support Provision"] = [
        big("Support records", S, COUNT),
        big("Met", S, sql_metric("COUNT(CASE WHEN is_met THEN 1 END)", "Met")),
        big("Fulfilment rate", S, pct("is_met", "% met")),
        pie("Records by support domain", S, ["support_domain"], COUNT),
        bar("Fulfilment rate by domain", S, "support_domain",
            [pct("is_met", "% met")]),
        bar("Support domain by severity", S, "disability_status_level",
            [COUNT], series=["support_domain"]),
        table("Provision by area and domain", S, ["geo_2", "support_domain"],
              [COUNT,
               sql_metric("COUNT(CASE WHEN is_unmet THEN 1 END)", "Unmet"),
               pct("is_met", "% met")]),
    ]

    # -- 3. Who is registered -------------------------------------------------
    d["Registry Profile"] = [
        big("People registered", P, COUNT),
        big("Severe or profound", P, pct_expr(
            "AVG(CASE WHEN disability_status_level IN ('SEVERE','PROFOUND') "
            "THEN 1.0 ELSE 0 END)", "% severe/profound")),
        big("Women and girls", P, pct("is_female", "% female")),
        big("Children under 15", P, pct_expr(
            "AVG(CASE WHEN age_band IN ('0-4','5-14') THEN 1.0 ELSE 0 END)",
            "% children")),
        pie("Primary impairment type", P, ["primary_impairment_type"], COUNT),
        pie("Severity level", P, ["disability_status_level"], COUNT),
        bar("Age band by sex", P, "age_band", [COUNT], series=["gender"], sort_desc=False),
        bar("Impairment type by sex", P, "primary_impairment_type", [COUNT],
            series=["gender"]),
        pie("Cause of impairment", P, ["primary_impairment_cause"], COUNT),
        bar("Age of onset", P, "primary_age_onset_band", [COUNT], sort_desc=False),
        table("Profile by area", P, ["geo_2"],
              [COUNT,
               pct("is_female", "% female"),
               pct_expr("AVG(CASE WHEN disability_status_level IN ('SEVERE','PROFOUND') "
                        "THEN 1.0 ELSE 0 END)", "% severe/profound"),
               pct("has_unmet_support_need", "% with unmet need")]),
    ]

    # -- 4. Programme coverage ------------------------------------------------
    d["Programme Coverage"] = [
        big("Enrolled in a programme", P, pct("currently_enrolled", "% enrolled")),
        big("Severe/profound but unenrolled", P, pct_expr(
            "AVG(CASE WHEN disability_status_level IN ('SEVERE','PROFOUND') "
            "AND NOT currently_enrolled THEN 1.0 "
            "WHEN disability_status_level IN ('SEVERE','PROFOUND') THEN 0.0 END)",
            "Severe, not enrolled")),
        big("Average programmes per person", P,
            simple("programme_count", "AVG", "Avg programmes")),
        # Coverage SHOULD rise with severity. A flat line here means the
        # programme is not reaching the people it was designed for.
        bar("Enrolment rate by severity", P, "disability_status_level",
            [pct("currently_enrolled", "% enrolled")], sort_desc=False),
        bar("Enrolment rate by support needs level", P, "support_needs_level",
            [pct("currently_enrolled", "% enrolled")], sort_desc=False),
        bar("Enrolment by area", P, "geo_2",
            [sql_metric("COUNT(CASE WHEN currently_enrolled THEN 1 END)", "Enrolled")]),
        table("Coverage gaps by area", P, ["geo_2"],
              [COUNT,
               pct("currently_enrolled", "% enrolled"),
               sql_metric("COUNT(CASE WHEN unmet_need_and_unenrolled THEN 1 END)",
                          "Unmet need, no programme")]),
    ]

    # -- 5. Inclusion ---------------------------------------------------------
    # The outcomes the UNCRPD is actually about — work, independent living,
    # legal capacity — rather than service counts.
    d["Inclusion & Independent Living"] = [
        big("In work", P, pct("is_in_work", "% in work")),
        big("In an institution", P, pct_expr(
            "AVG(CASE WHEN housing_type IN ('RESIDENTIAL_INSTITUTION',"
            "'HOSPITAL_LONG_STAY') THEN 1.0 ELSE 0 END)", "% institutionalised")),
        big("Under guardianship", P, pct_expr(
            "AVG(CASE WHEN legal_capacity_status IN ('PARTIAL_GUARDIANSHIP',"
            "'FULL_GUARDIANSHIP') THEN 1.0 ELSE 0 END)", "% under guardianship")),
        big("Homeless or in temporary shelter", P, pct_expr(
            "AVG(CASE WHEN housing_type IN ('HOMELESS','TEMPORARY_SHELTER') "
            "THEN 1.0 ELSE 0 END)", "% without stable housing")),
        pie("Employment status", P, ["employment_status"], COUNT),
        pie("Housing type", P, ["housing_type"], COUNT),
        bar("Employment rate by sex", P, "gender", [pct("is_in_work", "% in work")]),
        bar("Employment rate by severity", P, "disability_status_level",
            [pct("is_in_work", "% in work")], sort_desc=False),
        pie("Legal capacity status", P, ["legal_capacity_status"], COUNT),
        pie("Education level", P, ["education_level"], COUNT),
        table("Inclusion outcomes by sex", P, ["gender"],
              [COUNT,
               pct("is_in_work", "% in work"),
               pct("currently_enrolled", "% enrolled"),
               pct("has_unmet_support_need", "% with unmet need"),
               pct("has_legal_guardian", "% with a legal guardian")]),
    ]

    # -- 6. Care network ------------------------------------------------------
    # Unpaid family care is the invisible majority of disability support, and it
    # is invisible precisely because nobody counts it.
    d["Care Network"] = [
        big("With a primary caregiver", P, pct_expr(
            "AVG(CASE WHEN primary_caregiver_count > 0 THEN 1.0 ELSE 0 END)",
            "% with a caregiver")),
        big("Living alone", P, pct("lives_alone", "% living alone")),
        big("No caregiver, extensive needs", P, pct_expr(
            "AVG(CASE WHEN primary_caregiver_count = 0 AND support_needs_level IN "
            "('EXTENSIVE_SUPPORT','PERVASIVE_SUPPORT') THEN 1.0 "
            "WHEN support_needs_level IN ('EXTENSIVE_SUPPORT','PERVASIVE_SUPPORT') "
            "THEN 0.0 END)", "High need, no caregiver")),
        big("Needs human assistance", S, sql_metric(
            "COUNT(DISTINCT CASE WHEN support_domain = 'HUMAN_ASSISTANCE' "
            "AND is_unmet THEN person_id END)", "People")),
        bar("Caregiver presence by support needs level", P, "support_needs_level",
            [pct_expr("AVG(CASE WHEN primary_caregiver_count > 0 THEN 1.0 ELSE 0 END)",
                      "% with a caregiver")], sort_desc=False),
        bar("Human assistance need by area", S, "geo_2",
            [sql_metric("COUNT(CASE WHEN support_domain = 'HUMAN_ASSISTANCE' "
                        "AND is_unmet THEN 1 END)", "Unmet human assistance")]),
        table("Care gaps by area", P, ["geo_2"],
              [COUNT,
               pct_expr("AVG(CASE WHEN primary_caregiver_count > 0 THEN 1.0 ELSE 0 END)",
                        "% with a caregiver"),
               pct("lives_alone", "% living alone"),
               pct("has_legal_guardian", "% with a guardian")]),
    ]

    # -- 7. Register health ---------------------------------------------------
    # A disability register decays faster than most: certificates expire,
    # reassessment falls due, and a lapsed record silently stops entitling.
    d["Register Health"] = [
        big("Certificates expired", P, pct("certificate_expired", "% expired")),
        big("Reassessment overdue", P, pct("reassessment_overdue", "% overdue")),
        big("Awaiting assessment", P, pct_expr(
            "AVG(CASE WHEN disability_status = 'PENDING_ASSESSMENT' THEN 1.0 ELSE 0 END)",
            "% pending")),
        big("No impairment detail recorded", P, pct_expr(
            "AVG(CASE WHEN impairment_count = 0 THEN 1.0 ELSE 0 END)",
            "% missing detail")),
        pie("Assessment status", P, ["disability_status"], COUNT),
        pie("Registration channel", P, ["registration_channel"], COUNT),
        bar("Expired certificates by area", P, "geo_2",
            [sql_metric("COUNT(CASE WHEN certificate_expired THEN 1 END)", "Expired")]),
        table("Data completeness by area", P, ["geo_2"],
              [COUNT,
               pct_expr("AVG(CASE WHEN geo_3_id IS NOT NULL THEN 1.0 ELSE 0 END)",
                        "% geo-resolved"),
               pct_expr("AVG(CASE WHEN impairment_count > 0 THEN 1.0 ELSE 0 END)",
                        "% with impairment detail"),
               pct("certificate_expired", "% certificate expired"),
               pct("reassessment_overdue", "% reassessment overdue")]),
    ]

    return d


# ---------------------------------------------------------------------------
# YAML emitters
# ---------------------------------------------------------------------------
def dataset_yaml(name, db_uuid, columns):
    return {
        "table_name": name,
        "main_dttm_col": None,
        "description": f"Disability Registry reporting view {name}",
        "default_endpoint": None,
        "offset": 0,
        "cache_timeout": None,
        "schema": SCHEMA,
        "sql": None,
        "params": None,
        "template_params": None,
        "filter_select_enabled": True,
        "fetch_values_predicate": None,
        "extra": None,
        "normalize_columns": False,
        "always_filter_main_dttm": False,
        "uuid": uid("dataset", name),
        "metrics": [{
            "metric_name": "count",
            "verbose_name": "COUNT(*)",
            "metric_type": "count",
            "expression": "COUNT(*)",
            "description": None,
            "d3format": None,
            "currency": None,
            "extra": None,
            "warning_text": None,
        }],
        "columns": columns,
        "version": "1.0.0",
        "database_uuid": db_uuid,
    }


def column_entry(name, dtype):
    t = (dtype or "").upper()
    if "INT" in t:
        gen, is_dttm = "BIGINT", False
    elif any(k in t for k in ("DOUBLE", "NUMERIC", "REAL")):
        gen, is_dttm = "DOUBLE PRECISION", False
    elif "BOOL" in t:
        gen, is_dttm = "BOOLEAN", False
    elif "TIMESTAMP" in t or "DATE" in t:
        gen, is_dttm = "TIMESTAMP WITHOUT TIME ZONE", True
    else:
        gen, is_dttm = "VARCHAR", False
    return {
        "column_name": name,
        "verbose_name": None,
        "is_dttm": is_dttm,
        "is_active": True,
        "type": gen,
        "advanced_data_type": None,
        "groupby": True,
        "filterable": True,
        "expression": None,
        "description": None,
        "python_date_format": None,
        "extra": None,
    }


def chart_yaml(c, dataset_uuids):
    params = dict(c["params"])
    params.update({
        "datasource": f"{dataset_uuids[c['dataset']]}__table",
        "viz_type": c["viz_type"],
    })
    return {
        "slice_name": c["name"],
        # Superset shows this as an info icon beside the chart title, which is
        # where a reader who meets an "NA" slice will look first.
        "description": c.get("description"),
        "certified_by": None,
        "certification_details": None,
        "viz_type": c["viz_type"],
        # A mapping, not a JSON string. The REST API wants params serialised;
        # the YAML import format wants it structured, and passing a string here
        # fails validation with "Not a valid mapping type" on every chart.
        "params": params,
        "query_context": None,
        "cache_timeout": None,
        "uuid": uid("chart", c["name"]),
        "version": "1.0.0",
        "dataset_uuid": dataset_uuids[c["dataset"]],
    }


def dashboard_yaml(title, charts, native_filter_datasets):
    """Lay charts out two per row and attach a dashboard-wide gender filter."""
    pos = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    }
    # Big-number tiles are narrow; everything else takes half the 12-col grid.
    row, col_used, row_idx = [], 0, 0

    def flush():
        nonlocal row, col_used, row_idx
        if not row:
            return
        rid = f"ROW-{row_idx}"
        pos[rid] = {"type": "ROW", "id": rid, "children": [c[0] for c in row],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        pos["GRID_ID"]["children"].append(rid)
        for cid, meta in row:
            meta["parents"] = ["ROOT_ID", "GRID_ID", rid]
            pos[cid] = meta
        row, col_used, row_idx = [], 0, row_idx + 1

    for i, c in enumerate(charts):
        width = 3 if c["viz_type"] == "big_number_total" else 6
        height = 30 if c["viz_type"] == "big_number_total" else 50
        if col_used + width > 12:
            flush()
        cid = f"CHART-{i}"
        row.append((cid, {
            "type": "CHART", "id": cid, "children": [],
            "meta": {"chartId": 0, "width": width, "height": height,
                     "uuid": uid("chart", c["name"]), "sliceName": c["name"]},
        }))
        col_used += width
    flush()

    # Native filters. `gender` is the one the request called out — one control
    # that re-cuts every chart on the dashboard, which is cheaper than doubling
    # the chart count with male/female variants.
    filters = []
    for i, (col, label, ds) in enumerate(native_filter_datasets):
        filters.append({
            "id": f"NATIVE_FILTER-{uid('filter', title, col)[:8]}",
            "name": label,
            "filterType": "filter_select",
            "targets": [{"datasetUuid": ds, "column": {"name": col}}],
            "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}},
            "cascadeParentIds": [],
            "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
            "type": "NATIVE_FILTER",
            "description": "",
            "chartsInScope": [],
            "tabsInScope": [],
            "controlValues": {"multiSelect": True, "enableEmptyFilter": False,
                              "searchAllOptions": False, "inverseSelection": False},
        })

    return {
        "dashboard_title": title,
        "description": None,
        "css": "",
        "slug": None,
        "uuid": uid("dashboard", title),
        "position": pos,
        "metadata": {
            "color_scheme": None,
            "refresh_frequency": 0,
            "expanded_slices": {},
            "timed_refresh_immune_slices": [],
            "cross_filters_enabled": True,
            "native_filter_configuration": filters,
        },
        "version": "1.0.0",
    }


def fetch_columns(dsn, view):
    import psycopg2
    conn = psycopg2.connect(**dsn)
    with conn.cursor() as cur:
        # pg_catalog, not information_schema: the reporting layer is built from
        # MATERIALIZED views, and Postgres deliberately omits those from
        # information_schema.columns (they aren't in the SQL standard). Querying
        # information_schema here silently returns nothing.
        cur.execute(
            """
            select a.attname, format_type(a.atttypid, a.atttypmod)
            from pg_class c
            join pg_namespace n on n.oid = c.relnamespace
            join pg_attribute a on a.attrelid = c.oid
            where n.nspname = %s and c.relname = %s
              and c.relkind in ('r', 'v', 'm')
              and a.attnum > 0 and not a.attisdropped
            order by a.attnum
            """,
            (SCHEMA, view))
        cols = [column_entry(r[0], r[1]) for r in cur.fetchall()]
    conn.close()
    if not cols:
        raise SystemExit(
            f"view {view} not found in schema {SCHEMA} — run docker/db-seed/reporting_views.sql\n"
            f"against the registry database first; this builder reads the real column\n"
            f"list so the dataset it emits matches what Superset will query."
        )
    return cols


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Default straight into the chart. Helm's .Files.Get cannot reach outside
    # the chart directory, so that copy has to be the canonical one — keeping a
    # second copy here as well would just drift out of step with it.
    p.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "helm", "openg2p-disability-registry", "files", "dr-dashboards.zip"))
    p.add_argument("--db-name", default=DB_NAME)
    p.add_argument("--sqlalchemy-uri",
                   default="postgresql+psycopg2://postgres:XXXXX@commons-postgresql:5432/dr",
                   help="connection string recorded in the bundle; the password "
                        "is replaced at import time by Superset if left as a "
                        "placeholder, or override per environment")
    args = p.parse_args()

    dsn = dict(
        dbname=os.environ.get("DR_DB", "dr"),
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", ""),
    )

    db_uuid = uid("database", args.db_name)
    ds_uuids = {P: uid("dataset", P), S: uid("dataset", S)}

    files = {}
    files[f"{BUNDLE}/metadata.yaml"] = {
        "version": "1.0.0", "type": "Dashboard",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    files[f"{BUNDLE}/databases/{args.db_name}.yaml"] = {
        "database_name": args.db_name,
        "sqlalchemy_uri": args.sqlalchemy_uri,
        "cache_timeout": None,
        "expose_in_sqllab": True,
        "allow_run_async": False,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
        "allow_file_upload": False,
        # A dict, not a JSON string: the import schema loads `extra` as a nested
        # schema, so a string fails deep inside marshmallow with an unhelpful
        # "'str' object has no attribute 'get'".
        "extra": {"allows_virtual_table_explore": True},
        "uuid": db_uuid,
        "version": "1.0.0",
    }
    for view in (P, S):
        files[f"{BUNDLE}/datasets/{args.db_name}/{view}.yaml"] = dataset_yaml(
            view, db_uuid, fetch_columns(dsn, view))

    charts_by_dash = build_charts()
    seen = set()
    for title, charts in charts_by_dash.items():
        for c in charts:
            key = c["name"]
            if key in seen:
                # Chart names are the uuid seed, so duplicates would collapse
                # into one asset and silently vanish from a dashboard.
                raise SystemExit(f"duplicate chart name: {key!r}")
            seen.add(key)
            files[f"{BUNDLE}/charts/{slug(c['name'])}.yaml"] = chart_yaml(c, ds_uuids)

        # Native filters: one control that re-cuts every chart on the
        # dashboard, which is cheaper than doubling the chart count with
        # per-sex and per-area variants. Both views carry `gender` and `geo_2`
        # (the support view inherits them), so the filter is attached to
        # whichever dataset the dashboard's charts actually use.
        primary_ds = P if any(c["dataset"] == P for c in charts) else S
        nf = [
            ("gender", "Sex", ds_uuids[primary_ds]),
            ("geo_2", "Area", ds_uuids[primary_ds]),
        ]
        if any(c["dataset"] == S for c in charts):
            nf.append(("support_domain", "Support domain", ds_uuids[S]))
        files[f"{BUNDLE}/dashboards/{slug(title)}.yaml"] = dashboard_yaml(title, charts, nf)

    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        for path, doc in files.items():
            z.writestr(path, yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))

    n_charts = sum(len(v) for v in charts_by_dash.values())
    print(f"[bundle] {args.out}")
    print(f"[bundle] {len(charts_by_dash)} dashboards, {n_charts} charts, "
          f"{len(ds_uuids)} datasets")
    for t, cs in charts_by_dash.items():
        print(f"    {t:<38} {len(cs):>2} charts")


if __name__ == "__main__":
    main()
