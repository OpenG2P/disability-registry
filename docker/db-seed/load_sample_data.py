#!/usr/bin/env python3
"""Load sample data into the Disability Registry database.

Sources
-------
People (names, sex, birth date, geo, contacts) come from the SHARED demography
set — Master Data's country-pack samples when they exist, otherwise the CSV in
the openg2p-data clone the base image provides. Nothing about a person's
identity is invented here, so this registry's demo data lines up with the same
country pack every other OpenG2P registry uses.

The disability content comes from /seed/seed-data/disability_profiles.json.

Why archetypes instead of per-person fixture rows
-------------------------------------------------
The reference registries ship one JSON row per sample record and then have to
remap every foreign key when the demography set changes size. That coupling is
what makes their fixtures rot. Here each registered person is assigned ONE
archetype, chosen deterministically from a hash of their id, so:

  * the sample set is reproducible — the same person always gets the same
    profile, across re-runs and across environments;
  * it does not care how many people the demography source holds;
  * `unmet_support_needs_count` is DERIVED from the support rows actually
    inserted, so the denormalised summary can never contradict the detail.

Not everyone is registered
--------------------------
A disability registry holds people with disability, not the whole population.
`REGISTERED_SHARE` selects a deterministic subset of the demography set; the
default of 16% is the WHO/World Bank global disability prevalence estimate, so
population-level rates computed against a census denominator come out plausible.

Idempotent: re-running updates rows rather than duplicating them.
"""

import csv
import hashlib
import json
import os
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import psycopg2
from psycopg2.extras import Json, execute_values

SEEDER = "seeder"
CREATED_AT = "2026-04-01 00:00:00"

PERSON_TABLE = "g2p_register_persons_with_disability"
PERSON_REGISTER_MNEMONIC = "PersonWithDisability"

# child table -> (profile key, register mnemonic)
SUB_TABLES = [
    ("g2p_register_disability_details", "disability_details", "DisabilityDetail"),
    ("g2p_register_human_assistances", "human_assistance", "HumanAssistance"),
    ("g2p_register_assistive_technologies", "assistive_technology", "AssistiveTechnology"),
    ("g2p_register_medical_cares", "medical_care", "MedicalCare"),
    ("g2p_register_housing_supports", "housing_support", "HousingSupport"),
    ("g2p_register_animal_assistances", "animal_assistance", "AnimalAssistance"),
    ("g2p_register_related_persons", "related_persons", "RelatedPerson"),
    ("g2p_register_program_enrolments", "program_enrolments", "ProgramEnrolment"),
]

# Support statuses that count as an unmet need. Must match
# register_domain/services/utils/support_summary.py — the loader writes the
# summary directly (no ORM events fire for raw SQL), so the two definitions of
# "unmet" have to agree or the seeded data will disagree with anything the
# application later recomputes.
UNMET_STATUSES = {"REQUIRED", "PARTIALLY_RECEIVED"}

SUPPORT_KEYS = {
    "human_assistance",
    "assistive_technology",
    "medical_care",
    "housing_support",
    "animal_assistance",
}

OPENG2P_DATA_DIR = Path(os.environ.get("OPENG2P_DATA_DIR", "/openg2p-data"))
DEMO_DIR = OPENG2P_DATA_DIR / "demography"
SEED_DATA_DIR = Path(os.environ.get("DR_SEED_DATA_DIR", "/seed/seed-data"))

REGISTERED_SHARE = float(os.environ.get("DR_REGISTERED_SHARE", "0.16"))

# Stable across runs, so the same person always draws the same profile.
HASH_SALT = "openg2p-disability-registry"


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"[load-sample-data] Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def stable_fraction(key: str, namespace: str) -> float:
    """Deterministic value in [0, 1) for `key` within `namespace`.

    A hash rather than random.seed(): seeding a global RNG makes the result
    depend on how many draws happened earlier, so inserting one extra person
    would reshuffle everybody else's profile.
    """
    digest = hashlib.sha256(f"{HASH_SALT}:{namespace}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


# ── reading the demography set ───────────────────────────────────────────────


def read_csv_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append({k: (v if v != "" else None) for k, v in row.items()})
        return rows


def load_people() -> list[dict]:
    people = read_csv_rows(DEMO_DIR / "individuals.csv")
    if not people:
        print(
            "[load-sample-data] No demography source found at "
            f"{DEMO_DIR / 'individuals.csv'} — nothing to load.",
            file=sys.stderr,
        )
    return people


# ── geography ────────────────────────────────────────────────────────────────
# The demography CSV carries geography as NAMES (country, region, district,
# ward, village). The registry stores an id, plus the resolved hierarchy as
# JSONB — and the reporting views unpack that JSONB positionally into
# geo_1..geo_5, which is what every map and every geo chart groups by.
#
# So this has to be resolved, not computed. Only Master Data knows what its own
# ids are: seeded from a country pack, a unit's id is its P-code ("XK01010101"),
# while a slug-path computed from the names matches nothing. Nothing errors
# either — the names still read correctly, so the records look fine and simply
# never appear on a map.
#
# Resolution walks the name chain through parent links rather than matching
# names globally, because a village name repeats under different wards.
#
# Best effort by design: no MD_PG* env, an unreachable database or an empty
# table all mean the same thing — nothing to resolve against — and none of them
# should stop the sample load. Whichever path was taken is reported at the end.
GEO_NAME_COLUMNS = ["country", "region", "district", "ward", "village"]

_GEO_INDEX: dict[tuple[str, str], str] = {}
_GEO_STATS = {"resolved": 0, "unresolved": 0}


def load_geo_index() -> dict[tuple[str, str], str]:
    host = os.environ.get("MD_PGHOST")
    dbname = os.environ.get("MD_PGDATABASE")
    if not host or not dbname:
        print("[load-sample-data] MD_PG* not set — records will carry no geography.")
        return {}
    try:
        conn = psycopg2.connect(
            host=host,
            port=os.environ.get("MD_PGPORT", "5432"),
            dbname=dbname,
            user=os.environ.get("MD_PGUSER", ""),
            password=os.environ.get("MD_PGPASSWORD", ""),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[load-sample-data] master-data unreachable ({exc}) — no geography.")
        return {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select level_value_id, level_value_mnemonic, coalesce(parent_level_value_id, '') "
                "from g2p_geo_level_values"
            )
            index = {
                (parent, (name or "").strip().lower()): value_id
                for value_id, name, parent in cur.fetchall()
            }
    except Exception as exc:  # noqa: BLE001
        print(f"[load-sample-data] could not read master-data geo ({exc}) — no geography.")
        return {}
    finally:
        conn.close()
    print(f"[load-sample-data] master-data geo: {len(index)} units available for resolution.")
    return index


def resolve_geo(source: dict) -> tuple[str | None, dict | None]:
    """(lowest level_value_id, geo_code_hierarchy_json) for one source row.

    geo_code_hierarchy_json is written explicitly because the ORM's @validates
    hook that normally builds it fires only on ORM writes, never on the raw SQL
    this loader uses.
    """
    if not _GEO_INDEX:
        return None, None

    parent = ""
    hierarchy = []
    for column in GEO_NAME_COLUMNS:
        name = (source.get(column) or "").strip()
        if not name:
            break
        value_id = _GEO_INDEX.get((parent, name.lower()))
        if value_id is None:
            break
        hierarchy.append(
            {
                "level_id": column,
                "level_value_id": value_id,
                "level_value_mnemonic": name,
            }
        )
        parent = value_id

    if not hierarchy:
        _GEO_STATS["unresolved"] += 1
        return None, None
    _GEO_STATS["resolved"] += 1
    return hierarchy[-1]["level_value_id"], {"hierarchy": hierarchy}


def report_geo_resolution() -> None:
    resolved, unresolved = _GEO_STATS["resolved"], _GEO_STATS["unresolved"]
    if not resolved and not unresolved:
        return
    print(f"[load-sample-data] geography: {resolved} resolved, {unresolved} unresolved.")
    if resolved == 0:
        print(
            "[load-sample-data] WARNING: no record carries geography, so every map "
            "and every geo-grouped chart will be empty. Load a country pack into "
            "Master Data (geoSeed.countryPack) and re-run."
        )


# ── schema introspection ─────────────────────────────────────────────────────


def table_columns(cur, table: str) -> dict[str, str]:
    """Column name -> data type for `table`.

    Read from the database rather than hard-coded so that adding a column to the
    ORM does not silently break this loader, and so a column removed upstream
    does not make it fail on an INSERT naming a column that no longer exists.
    """
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s",
        (table,),
    )
    return {name: dtype for name, dtype in cur.fetchall()}


def get_register_id(cur, mnemonic: str) -> str | None:
    cur.execute(
        "SELECT register_id FROM g2p_register_definitions WHERE register_mnemonic = %s",
        (mnemonic,),
    )
    row = cur.fetchone()
    return row[0] if row else None


# ── row construction ─────────────────────────────────────────────────────────


def coerce(value, dtype: str):
    if value is None:
        return None
    if dtype in ("jsonb", "json"):
        if not isinstance(value, str):
            return Json(value)
        text = value.strip()
        if not text:
            return None
        # The demography CSV is not uniformly JSON in its JSON columns:
        # `phone_numbers` holds a serialised list of objects, but `emails` holds
        # a single bare address. json.loads on the latter raises, which took the
        # whole load down. Parse what parses; wrap a bare scalar as a
        # one-element list, which is the shape every list-valued column here
        # (emails, alias_names, phone_numbers) expects.
        if text[0] in "[{":
            try:
                return Json(json.loads(text))
            except json.JSONDecodeError:
                pass
        return Json([text])
    if dtype == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y"}
    return value


def project(row: dict, columns: dict[str, str]) -> dict:
    """Keep only keys that are real columns, coercing to the column's type."""
    return {k: coerce(v, columns[k]) for k, v in row.items() if k in columns}


def insert_rows(cur, table: str, rows: list[dict], columns: dict[str, str]) -> int:
    if not rows:
        return 0
    keys = sorted({k for row in rows for k in row})
    updatable = [k for k in keys if k != "internal_record_id"]
    column_list = ", ".join(f'"{k}"' for k in keys)
    update_list = ", ".join(f'"{k}" = EXCLUDED."{k}"' for k in updatable)
    statement = (
        f'INSERT INTO "public"."{table}" ({column_list}) VALUES %s '
        f'ON CONFLICT ("internal_record_id") DO UPDATE SET {update_list}'
    )
    values = [tuple(row.get(k) for k in keys) for row in rows]
    execute_values(cur, statement, values)
    return len(values)


def build_person(source: dict, profile: dict, columns: dict[str, str]) -> dict:
    """One person row, merging demography identity with the profile's disability."""
    source_id = str(source.get("functional_record_id") or source.get("internal_record_id") or "")
    internal_record_id = str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"{HASH_SALT}:person:{source_id}")
    )
    serial = int(stable_fraction(source_id, "serial") * 1_000_000_000)
    functional_record_id = f"PWD-{serial:012d}"

    first_name = source.get("first_name") or ""
    last_name = source.get("last_name") or ""
    full_name = " ".join(part for part in (first_name, last_name) if part)

    row = dict(source)
    row.update(profile.get("person") or {})
    row.update(
        {
            "internal_record_id": internal_record_id,
            "functional_record_id": functional_record_id,
            "full_name": full_name,
            "record_name": full_name or functional_record_id,
            "record_status": "ACTIVE",
            "created_by": SEEDER,
            "created_at": CREATED_AT,
            "last_approved_at": CREATED_AT,
            "last_approved_by": SEEDER,
            "registration_channel": "ASSISTED_REGISTRATION",
            "identity_evidence_type": "FOUNDATIONAL_ID_VERIFIED"
            if source.get("foundational_id")
            else "NONE",
        }
    )

    # search_text is normally populated by SQLAlchemy event listeners, which do
    # NOT fire for raw SQL. Written explicitly here, and it carries the SOURCE
    # demography id as well — upload_images.py joins on that to attach photos.
    row["search_text"] = " ".join(
        str(part)
        for part in (
            functional_record_id,
            source_id,
            full_name,
            source.get("foundational_id") or "",
            source.get("birth_date") or "",
        )
        if part
    )

    assessment = _assessment_dates(source_id, row.get("disability_status"))
    row.update(assessment)

    geo_value_id, geo_hierarchy = resolve_geo(source)
    row["geo_lowest_level_value_id"] = geo_value_id
    row["geo_code_hierarchy_json"] = geo_hierarchy

    return project(row, columns)


def _assessment_dates(key: str, status) -> dict:
    """Assessment and certificate dates, spread over the last few years.

    A registry where every certificate was issued on the same day produces a
    renewal cliff and a meaningless expiry chart, so these are staggered
    deterministically.
    """
    if status == "PENDING_ASSESSMENT":
        return {}
    days_ago = int(stable_fraction(key, "assessment") * 1460)  # up to ~4 years
    assessed = date(2026, 1, 1) - timedelta(days=days_ago)
    return {
        "assessment_date": assessed.isoformat(),
        "assessment_authority": "MEDICAL_BOARD",
        "disability_certificate_number": f"DC-{assessed.year}-{abs(hash(key)) % 100000:05d}",
        "certificate_issue_date": (assessed + timedelta(days=14)).isoformat(),
        "certificate_expiry_date": (assessed + timedelta(days=14 + 1825)).isoformat(),
        "next_reassessment_date": (assessed + timedelta(days=1825)).isoformat(),
    }


def build_children(person_id: str, source_id: str, profile: dict, columns_by_table: dict):
    """Child rows for one person, plus the unmet-need count they imply."""
    out: dict[str, list[dict]] = {}
    unmet = 0
    for table, profile_key, _mnemonic in SUB_TABLES:
        rows = []
        for index, template in enumerate(profile.get(profile_key) or []):
            row = dict(template)
            row.update(
                {
                    "internal_record_id": str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"{HASH_SALT}:{table}:{source_id}:{index}",
                        )
                    ),
                    "link_internal_record_id": person_id,
                    "record_status": "ACTIVE",
                    "created_by": SEEDER,
                    "created_at": CREATED_AT,
                    "last_approved_at": CREATED_AT,
                    "last_approved_by": SEEDER,
                    "registration_date": "2024-01-15",
                }
            )
            row.setdefault("record_name", _child_record_name(profile_key, template))
            row["search_text"] = row["record_name"]
            if profile_key in SUPPORT_KEYS and row.get("support_status") in UNMET_STATUSES:
                unmet += 1
            rows.append(project(row, columns_by_table[table]))
        if rows:
            out[table] = rows
    return out, unmet


def _child_record_name(profile_key: str, template: dict) -> str:
    for key in (
        "impairment_type",
        "assistance_type",
        "assistive_technology_type",
        "medical_care_type",
        "housing_support_type",
        "animal_assistance_type",
        "relationship_type",
        "program_name",
    ):
        if template.get(key):
            status = template.get("support_status") or template.get("enrolment_status") or ""
            return f"{template[key]} {status}".strip()
    return profile_key


def pick_profile(source_id: str, profiles: list[dict]) -> dict:
    """Weighted deterministic choice."""
    total = sum(p.get("weight", 1) for p in profiles)
    target = stable_fraction(source_id, "profile") * total
    running = 0.0
    for profile in profiles:
        running += profile.get("weight", 1)
        if target < running:
            return profile
    return profiles[-1]


# ── SUPPORT_NEED score ───────────────────────────────────────────────────────
# The AUTHORITATIVE implementation is
# disability-extension/.../score_compute/services/support_need.py, run by the
# celery worker. This is a mirror of it, for one reason: without a seeded score
# every score tile and the map's colour scale are blank until a worker has drained
# the queue, and a demo environment that looks broken is worse than no demo.
#
# The worker OVERWRITES these on its first compute, so a small divergence is
# self-correcting rather than permanent. The weights are read from the metadata
# this same run seeded, so only the ordinal maps are duplicated — keep them in
# step with the service (test/test_metadata_consistency.py does not cover this;
# a mismatch shows up as scores that jump once the worker starts).
_ORDINAL_SCALES = {
    "disability_status_level": {
        "NONE": 0.0, "MILD": 0.25, "MODERATE": 0.5, "SEVERE": 0.75, "PROFOUND": 1.0,
    },
    "support_needs_level": {
        "INDEPENDENT": 0.0, "INTERMITTENT_SUPPORT": 0.25, "LIMITED_SUPPORT": 0.5,
        "EXTENSIVE_SUPPORT": 0.75, "PERVASIVE_SUPPORT": 1.0,
    },
}
_UNMET_NEEDS_CEILING = 5.0
_SCORE_TYPE = "SUPPORT_NEED"
_SCORE_TRIGGER = "seed"


def _normalise_contributor(key, value) -> float:
    if value is None:
        return 0.0
    scale = _ORDINAL_SCALES.get(key)
    if scale is not None:
        return scale.get(str(value).strip().upper(), 0.0)
    if key == "unmet_support_needs_count":
        try:
            return min(float(value) / _UNMET_NEEDS_CEILING, 1.0)
        except (TypeError, ValueError):
            return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return 0.0


def insert_scores(cur, register_id, people: list[dict]) -> None:
    """Seed one SUPPORT_NEED score per person, from the configured weights."""
    if not register_id or not people:
        return

    cur.execute(
        "SELECT score_definition_id FROM g2p_register_score_definitions "
        "WHERE register_mnemonic = %s AND score_type = %s",
        (PERSON_REGISTER_MNEMONIC, _SCORE_TYPE),
    )
    row = cur.fetchone()
    if not row:
        print("[load-sample-data] no SUPPORT_NEED score definition — scores skipped")
        return
    score_definition_id = row[0]

    cur.execute(
        "SELECT attribute_name, attribute_weightage "
        "FROM g2p_register_score_contributing_attributes "
        "WHERE register_mnemonic = %s AND score_type = %s",
        (PERSON_REGISTER_MNEMONIC, _SCORE_TYPE),
    )
    weights = {name: float(weight) for name, weight in cur.fetchall()}
    if not weights:
        print("[load-sample-data] no contributing attributes — scores skipped")
        return

    total_weight = sum(weights.values())
    rows = []
    for person in people:
        score = sum(
            _normalise_contributor(key, person.get(key)) * weight
            for key, weight in weights.items()
        )
        # Rescaled by total weight, exactly as the service does, so adding a
        # contributor does not silently shift every previously computed score.
        if total_weight > 0:
            score /= total_weight
        rows.append(
            (
                str(uuid.uuid5(uuid.NAMESPACE_URL,
                               f"{HASH_SALT}:score:{person['internal_record_id']}")),
                register_id,
                _SCORE_TYPE,
                score_definition_id,
                person["internal_record_id"],
                # NOT NULL, but not a foreign key: it records WHAT triggered the
                # computation. A seeded score was triggered by the seed, so it is
                # marked as such rather than pointed at a change request that
                # never happened.
                _SCORE_TRIGGER,
                None,
                round(score, 4),
                CREATED_AT,
            )
        )

    columns = [
        "internal_record_id", "register_id", "score_type", "score_definition_id",
        "link_internal_record_id", "triggered_by_cr_id", "triggered_by_submission_id",
        "computed_score", "computed_at",
    ]
    try:
        cur.execute("SAVEPOINT seed_scores")
        execute_values(
            cur,
            'INSERT INTO "public"."g2p_register_scores" ('
            + ", ".join(f'"{c}"' for c in columns)
            # Conflict target is the UNIQUE (link_internal_record_id, score_type)
            # index, not the primary key: one score of a type per person is the
            # real constraint, and a re-run must update that row rather than
            # trip over it.
            + ') VALUES %s ON CONFLICT ("link_internal_record_id", "score_type") '
              'DO UPDATE SET "computed_score" = EXCLUDED."computed_score", '
              '"computed_at" = EXCLUDED."computed_at"',
            rows,
        )
        cur.execute("RELEASE SAVEPOINT seed_scores")
        print(f"[load-sample-data]   g2p_register_scores: {len(rows)} row(s)")
    except psycopg2.Error as exc:
        cur.execute("ROLLBACK TO SAVEPOINT seed_scores")
        print(f"[load-sample-data] score seeding skipped: {exc}")


def enqueue_completion_scores(cur, register_id: str | None, record_ids: list[str]) -> None:
    """Queue section-completion computation for every seeded record.

    The queue is keyed per (record, SECTION), not per record: completion is
    scored a section at a time, so one row per record would leave every section
    but one uncomputed. Sections are read from the metadata this same seed run
    just inserted rather than listed here, so adding a section needs no change.

    Wrapped in a SAVEPOINT: this is a nice-to-have, and on an older platform pin
    whose queue table has a different shape it must not take the whole sample
    load down with it. Without the savepoint the failed statement would poison
    the surrounding transaction and the commit below would roll everything back.
    """
    if not register_id or not record_ids:
        return

    cur.execute(
        "SELECT section_id FROM g2p_register_sections WHERE register_id = %s",
        (register_id,),
    )
    section_ids = [row[0] for row in cur.fetchall()]
    if not section_ids:
        print("[load-sample-data] no sections found — completion-score queue skipped")
        return

    rows = [
        (str(uuid.uuid4()), register_id, record_id, section_id, "PENDING", 0)
        for record_id in record_ids
        for section_id in section_ids
    ]
    try:
        cur.execute("SAVEPOINT completion_queue")
        execute_values(
            cur,
            'INSERT INTO "public"."g2p_completion_score_computation_queue" '
            '("queue_id","register_id","internal_record_id","section_id",'
            '"compute_status","compute_number_of_attempts") VALUES %s '
            "ON CONFLICT DO NOTHING",
            rows,
        )
        cur.execute("RELEASE SAVEPOINT completion_queue")
        print(
            f"[load-sample-data] queued completion scoring for {len(record_ids)} record(s) "
            f"x {len(section_ids)} section(s)"
        )
    except psycopg2.Error as exc:
        cur.execute("ROLLBACK TO SAVEPOINT completion_queue")
        print(f"[load-sample-data] completion-score queue skipped: {exc}")


def main() -> None:
    people = load_people()
    if not people:
        return

    profiles_doc = json.loads((SEED_DATA_DIR / "disability_profiles.json").read_text())
    profiles = profiles_doc["profiles"]

    # Read once; every record resolves against this rather than reopening
    # master-data per row.
    global _GEO_INDEX
    _GEO_INDEX = load_geo_index()

    conn = psycopg2.connect(
        host=env("PGHOST"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=env("PGDATABASE"),
        user=env("PGUSER"),
        password=env("PGPASSWORD"),
    )
    conn.autocommit = False
    cur = conn.cursor()

    try:
        person_columns = table_columns(cur, PERSON_TABLE)
        if not person_columns:
            print(
                f"[load-sample-data] Table {PERSON_TABLE} does not exist — the API "
                "migration has not run yet. Nothing loaded.",
                file=sys.stderr,
            )
            sys.exit(1)
        columns_by_table = {t: table_columns(cur, t) for t, _, _ in SUB_TABLES}

        person_rows: list[dict] = []
        children: dict[str, list[dict]] = {}
        counts: dict[str, int] = {}
        skipped = 0

        for source in people:
            source_id = str(
                source.get("functional_record_id") or source.get("internal_record_id") or ""
            )
            if not source_id:
                skipped += 1
                continue
            # Only a share of the population is registered here.
            if stable_fraction(source_id, "registered") >= REGISTERED_SHARE:
                continue

            profile = pick_profile(source_id, profiles)
            person = build_person(source, profile, person_columns)
            child_rows, unmet = build_children(
                person["internal_record_id"], source_id, profile, columns_by_table
            )

            if "unmet_support_needs_count" in person_columns:
                person["unmet_support_needs_count"] = unmet
            if "has_unmet_support_need" in person_columns:
                person["has_unmet_support_need"] = unmet > 0

            person_rows.append(person)
            for table, rows in child_rows.items():
                children.setdefault(table, []).extend(rows)
            counts[profile["code"]] = counts.get(profile["code"], 0) + 1

        inserted = insert_rows(cur, PERSON_TABLE, person_rows, person_columns)
        print(
            f"[load-sample-data] {inserted} person(s) registered "
            f"out of {len(people)} in the demography set "
            f"({REGISTERED_SHARE:.0%} target share)."
        )
        if skipped:
            print(f"[load-sample-data] skipped {skipped} source row(s) with no id.")

        for table, _profile_key, _mnemonic in SUB_TABLES:
            rows = children.get(table, [])
            if rows:
                insert_rows(cur, table, rows, columns_by_table[table])
                print(f"[load-sample-data]   {table}: {len(rows)} row(s)")

        unmet_total = sum(
            1 for person in person_rows if person.get("has_unmet_support_need")
        )
        print(
            f"[load-sample-data] {unmet_total} person(s) with at least one unmet "
            f"support need."
        )
        print("[load-sample-data] profile distribution:")
        for code, count in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"[load-sample-data]   {code:26} {count}")

        person_register_id = get_register_id(cur, PERSON_REGISTER_MNEMONIC)
        insert_scores(cur, person_register_id, person_rows)
        enqueue_completion_scores(
            cur,
            person_register_id,
            [person["internal_record_id"] for person in person_rows],
        )

        conn.commit()
        report_geo_resolution()
        print("[load-sample-data] Done.")
    except Exception as exc:
        conn.rollback()
        print(f"[load-sample-data] FAILED: {exc}", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
