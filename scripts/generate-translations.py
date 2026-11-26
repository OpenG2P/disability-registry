#!/usr/bin/env python3
"""Regenerate translation/domain.json and the English registry_languages row.

Why this exists
---------------
Every `widget-label` and `section-title` in `g2p_register_sections.sql`, and every
enum value that reaches a dropdown, is a translation KEY. The staff portal renders
the raw key when the language row has no entry for it — so a field added without
a matching translation shows up in the UI as `assistive_technology_type` instead
of "Assistive Technology Type". Nothing errors; the screen just looks unfinished.

Keeping that list by hand is what makes it rot, so it is derived from the
metadata that actually drives the UI. Human-written labels already in
translation/domain.json are PRESERVED — this only ever adds missing keys and
drops keys the UI no longer references.

The generated English row is then written into
meta_data/registry-configurations/g2p_registry_languages.sql, which is what the
db-seed job loads. Additional languages are added through the staff portal's
language editor (or by extending LANGUAGES below) — they are translations of
this same key set.

Usage:  ./scripts/generate-translations.py [--check]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
EXT = REPO / "disability-extension/src/openg2p_registry_disability_extension"
SECTIONS_SQL = EXT / "meta_data/register-metadata/g2p_register_sections.sql"
TABS_SQL = EXT / "meta_data/register-metadata/g2p_register_ui_tabs.sql"
SCHEMAS_SQL = EXT / "meta_data/register-metadata/g2p_register_schemas.sql"
REGISTERS_SQL = EXT / "meta_data/register-metadata/g2p_register_definitions.sql"
SCORES_SQL = EXT / "meta_data/register-metadata/g2p_register_score_definitions.sql"
LOOKUP_DIR = EXT / "meta_data/lookup-data"
CONFIG_SQL = EXT / "meta_data/registry-configurations/g2p_registry_configuration.sql"
ENUMS = EXT / "register_domain/models/enums.py"
LANGUAGES_SQL = EXT / "meta_data/registry-configurations/g2p_registry_languages.sql"
DOMAIN_JSON = REPO / "translation/domain.json"

# language_id is frozen: the configuration row references it.
LANGUAGES = [
    ("ccbcb97b-c4df-415d-9e4d-ec4985cf04e9", "en", "English", True),
]

# Keys whose Title Case default reads badly, plus UI actions that appear in the
# portal chrome rather than in the section metadata.
OVERRIDES = {
    "age_on_set": "Age at Onset",
    "self_id_disability": "Self-identifies as having a disability",
    "has_unmet_support_need": "Has Unmet Support Need",
    "unmet_support_needs_count": "Number of Unmet Support Needs",
    "monthly_out_of_pocket_cost": "Monthly Out-of-pocket Cost",
    "is_covered_by_insurance": "Covered by Insurance",
    "functional_record_id": "Person ID",
    "foundational_id": "Foundational ID",
    "foundational_id_masked": "Foundational ID (masked)",
    "plus_code": "Plus Code",
    "geo_code_hierarchy_json": "Location",
    "location": "Location",
    # The register list page's breadcrumb is the lower-cased register mnemonic
    # from the URL (/register/personwithdisability), looked up as a key.
    "personwithdisability": "Person with Disability",
    "SUPPORT_NEED": "Support Need",
    "FOUNDATIONAL_ID_VERIFIED": "Foundational ID verified",
    "add_disability_detail": "Add Impairment",
    "add_human_assistance": "Add Human Assistance",
    "add_assistive_technology": "Add Assistive Technology",
    "add_medical_care": "Add Medical Care",
    "add_housing_support": "Add Housing Support",
    "add_animal_assistance": "Add Animal Assistance",
    "add_related_person": "Add Related Person",
    "add_program_enrolment": "Add Programme Enrolment",
    "WHODAS_2_0": "WHODAS 2.0",
    "OPD_REFERRAL": "Referral from an organisation of persons with disabilities",
    "EARLY_CHILDHOOD_0_5": "Early childhood (0-5)",
    "CHILDHOOD_6_12": "Childhood (6-12)",
    "ADOLESCENCE_13_17": "Adolescence (13-17)",
    "ADULTHOOD_18_59": "Adulthood (18-59)",
    "OLD_AGE_60_PLUS": "Old age (60+)",
}

# Actions the table widgets render, one per list section.
TABLE_ACTIONS = [
    "add_disability_detail",
    "add_human_assistance",
    "add_assistive_technology",
    "add_medical_care",
    "add_housing_support",
    "add_animal_assistance",
    "add_related_person",
    "add_program_enrolment",
]

# Record lifecycle values the portal shows on every register.
RECORD_STATUSES = ["ACTIVE", "INACTIVE", "ARCHIVED", "DRAFT", "PENDING"]

# Labels the platform's record view and header pass through the translator with
# no namespace. They are English already, so they translate to themselves; the
# entry exists so the lookup resolves (and so another language can override it)
# instead of logging MISSING_MESSAGE on every record view.
PORTAL_LABELS = [
    "Functional Record ID",
    "Record Status",
    "Status Reason",
    "Created by",
    "Created at",
    "Last Approved by",
    "Last Approved at",
    "Not set",
    # Edit forms: the dropdown placeholder and the change-reason prompt.
    "Select",
    "Enter Reason",
]


def sql_literals(text: str) -> list[str]:
    """Every single-quoted SQL literal, handling '' escaping."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "'":
            j, buf = i + 1, []
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(text[j])
                j += 1
            out.append("".join(buf))
            i = j + 1
        else:
            i += 1
    return out


def walk(node, keys: set[str]) -> None:
    if isinstance(node, dict):
        for field in ("widget-label", "section-title"):
            value = node.get(field)
            if isinstance(value, str) and value:
                keys.add(value)
        for value in node.values():
            walk(value, keys)
    elif isinstance(node, list):
        for item in node:
            walk(item, keys)


def ui_keys() -> set[str]:
    keys: set[str] = set()
    for literal in sql_literals(SECTIONS_SQL.read_text()):
        if literal.startswith("{"):
            walk(json.loads(literal), keys)
    return keys


def enum_keys() -> set[str]:
    spec = importlib.util.spec_from_file_location("dr_enums", ENUMS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import enum as _enum

    keys: set[str] = set()
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, _enum.Enum) and obj is not _enum.Enum:
            keys.update(member.value for member in obj)
    return keys


def insert_rows(path: pathlib.Path) -> list[dict[str, str | None]]:
    """Rows of every `INSERT INTO ... (cols) VALUES (...), ...` in a seed file,
    as column -> value. Literals are unquoted; NULL becomes None; numbers and
    other bare tokens are kept as text. Enough for the flat seed files here."""
    text = path.read_text()
    rows: list[dict[str, str | None]] = []
    for m in re.finditer(r"INSERT INTO\s+\S+\s*\(([^)]*)\)\s*VALUES", text, re.I):
        columns = [c.strip().strip('"') for c in m.group(1).split(",")]
        i, n = m.end(), len(text)
        while i < n:
            while i < n and text[i] in " \t\r\n,":
                i += 1
            if i >= n or text[i] != "(":
                break  # ON CONFLICT ... — end of this VALUES list
            i += 1
            values: list[str | None] = []
            while True:
                while text[i] in " \t\r\n":
                    i += 1
                if text[i] == "'":
                    j, buf = i + 1, []
                    while True:
                        if text[j] == "'":
                            if text[j + 1] == "'":
                                buf.append("'")
                                j += 2
                                continue
                            break
                        buf.append(text[j])
                        j += 1
                    values.append("".join(buf))
                    i = j + 1
                else:
                    j = i
                    while text[j] not in ",)":
                        j += 1
                    token = text[i:j].strip()
                    values.append(None if token.upper() == "NULL" else token)
                    i = j
                while text[i] in " \t\r\n":
                    i += 1
                if text[i] == ",":
                    i += 1
                    continue
                if text[i] == ")":
                    i += 1
                    break
            rows.append(dict(zip(columns, values)))
    return rows


def tab_keys() -> set[str]:
    """Tab labels are stored as keys (`person_tab`) and rendered through the
    translator, exactly like section titles."""
    return {r["tab_label"] for r in insert_rows(TABS_SQL) if r.get("tab_label")}


def code_list_labels() -> dict[str, str]:
    """value_code -> label for every code-list value the registry seeds,
    including the platform lists (GENDER, MARITAL_STATUS, ...) that have no
    enum here. Dropdowns show value_display and translate it, so the code must
    be a key. A curated list whose display is already readable keeps it;
    a generated one (display == code) is humanised."""
    labels: dict[str, str] = {}
    for path in sorted(LOOKUP_DIR.glob("g2p_attribute_values*.sql")):
        for r in insert_rows(path):
            code, display = r.get("value_code"), r.get("value_display")
            if not code:
                continue
            if display and display != code and not display.isupper():
                labels.setdefault(code, display)
            else:
                labels.setdefault(code, humanise(code))
    return labels


def list_field_labels() -> dict[str, str]:
    """field_name -> display_label for the register list's result columns and
    filters. The list page renders field_name through the translator, so a
    field shown there but bound to no widget (functional_record_id) would
    otherwise appear as the raw column name."""
    labels: dict[str, str] = {}
    for row in insert_rows(SCHEMAS_SQL):
        for column in ("search_result_schema", "filter_schema"):
            raw = row.get(column)
            if not raw:
                continue
            for field in json.loads(raw):
                name = field.get("field_name")
                if name:
                    labels.setdefault(name, field.get("display_label") or humanise(name))
    return labels


def score_type_keys() -> set[str]:
    """The record's score widget shows each score_type through the translator."""
    return {r["score_type"] for r in insert_rows(SCORES_SQL) if r.get("score_type")}


def register_names() -> set[str]:
    """Register subjects and the registry name are rendered through the
    translator as-is (home tiles, breadcrumbs, the portal header)."""
    names = {r["register_subject"] for r in insert_rows(REGISTERS_SQL) if r.get("register_subject")}
    names |= {r["registry_name"] for r in insert_rows(CONFIG_SQL) if r.get("registry_name")}
    return names


def humanise(key: str) -> str:
    if key in OVERRIDES:
        return OVERRIDES[key]
    if key.isupper():
        # Enum value: SEVERE_IMPAIRMENT -> "Severe impairment"
        words = key.replace("_", " ").lower()
        return words[0].upper() + words[1:] if words else key
    label = re.sub(r"[_\s]+", " ", key).strip().title()
    # Title() capitalises every word, which reads wrong in a section heading
    # ("Disability Status And Assessment"). Lower the joining words back down,
    # except when one starts the label.
    for small in ("And", "Or", "Of", "To", "For", "In", "With", "The", "A", "An"):
        label = re.sub(rf"(?<!^)\b{small}\b", small.lower(), label)
    return label


def build() -> dict[str, str]:
    code_lists = code_list_labels()
    list_fields = list_field_labels()
    value_keys = enum_keys() | set(code_lists) | set(RECORD_STATUSES)
    keys = (
        ui_keys()
        | tab_keys()
        | set(list_fields)
        | value_keys
        | score_type_keys()
        | set(TABLE_ACTIONS)
        | {"personwithdisability"}
    )
    existing: dict[str, str] = {}
    if DOMAIN_JSON.exists():
        existing = json.loads(DOMAIN_JSON.read_text())

    tabs = tab_keys()
    result = {}
    for key in sorted(keys, key=str.lower):
        # An override always wins, so correcting a bad default here actually
        # takes effect. Otherwise a human edit already in the file is kept,
        # then a curated code-list display, then the humanised key.
        if key in OVERRIDES:
            result[key] = OVERRIDES[key]
        elif key in tabs:
            # person_tab -> "Person": the tab strip already says these are tabs.
            result[key] = existing.get(key) or humanise(key.removesuffix("_tab"))
        else:
            result[key] = (
                existing.get(key) or code_lists.get(key) or list_fields.get(key) or humanise(key)
            )

    # Strings that reach the translator already in their final, readable form:
    # the portal's own record labels, register/registry names, and every label
    # produced above — the read-only select/checkbox widgets and the edit forms
    # translate a field or option label that was already translated once. Each
    # maps to itself unless a human already gave it a different text.
    identity = set(PORTAL_LABELS) | register_names() | set(result.values())
    for label in sorted(identity, key=str.lower):
        if label not in result:
            result[label] = existing.get(label) or label
    return dict(sorted(result.items(), key=lambda kv: kv[0].lower()))


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_languages_sql(translations: dict[str, str]) -> str:
    payload = json.dumps(translations, ensure_ascii=False, sort_keys=True)
    rows = []
    for language_id, code, label, is_default in LANGUAGES:
        rows.append(
            "("
            + ",".join(
                [
                    sql_quote(language_id),
                    sql_quote(code),
                    sql_quote(label),
                    sql_quote(""),  # language_flag_base64 — set in the staff portal
                    "'TRUE'" if is_default else "'FALSE'",
                    sql_quote("{}"),  # core_translation ships with the platform UI
                    sql_quote(payload),
                ]
            )
            + ")"
        )
    return (
        "-- Registry languages — GENERATED, do not hand-edit.\n"
        "--\n"
        "-- Regenerate with ./scripts/generate-translations.py, which derives the\n"
        "-- domain_translation key set from the section widgets, tab labels, code\n"
        "-- lists, score types and register names in this extension's metadata and\n"
        "-- the values in models/enums.py. A key the UI references but this row\n"
        "-- lacks is rendered raw in the staff portal and logged as MISSING_MESSAGE.\n"
        "--\n"
        "-- core_translation is left empty on purpose: the platform UI ships its own.\n"
        "-- Additional languages are added through the staff portal's language editor.\n"
        "--\n"
        "-- Re-running MERGES rather than skipping: keys added here reach an existing\n"
        "-- install on upgrade, while any value already in the database (including\n"
        "-- one edited in the staff portal) is kept.\n"
        'INSERT INTO "public"."registry_languages" ("language_id","language_code","language_label",'
        '"language_flag_base64","is_default","core_translation","domain_translation") VALUES \n'
        + ",\n".join(rows)
        + "\n"
        + 'ON CONFLICT ("language_id") DO UPDATE SET "domain_translation" = (\n'
        + '    EXCLUDED."domain_translation"::jsonb\n'
        + '    || COALESCE("registry_languages"."domain_translation"::jsonb, \'{}\'::jsonb)\n'
        + ")::json;\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if checked-in files are stale")
    args = parser.parse_args()

    translations = build()
    domain_json = json.dumps(translations, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    languages_sql = render_languages_sql(translations)

    targets = {DOMAIN_JSON: domain_json, LANGUAGES_SQL: languages_sql}
    stale = [p for p, content in targets.items() if not p.exists() or p.read_text() != content]

    if args.check:
        if stale:
            for path in stale:
                print(f"STALE: {path.relative_to(REPO)}", file=sys.stderr)
            print("\nRun ./scripts/generate-translations.py to regenerate.", file=sys.stderr)
            return 1
        print(f"translations up to date ({len(translations)} keys)")
        return 0

    DOMAIN_JSON.parent.mkdir(parents=True, exist_ok=True)
    for path, content in targets.items():
        path.write_text(content)
    print(f"wrote {len(translations)} translation keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
