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
    "admin_level_1": "Administrative Level 1",
    "admin_level_2": "Administrative Level 2",
    "admin_level_3": "Administrative Level 3",
    "admin_level_4": "Administrative Level 4",
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
    keys = ui_keys() | enum_keys() | set(TABLE_ACTIONS) | set(RECORD_STATUSES)
    existing: dict[str, str] = {}
    if DOMAIN_JSON.exists():
        existing = json.loads(DOMAIN_JSON.read_text())

    result = {}
    for key in sorted(keys, key=str.lower):
        # An override always wins, so correcting a bad default here actually
        # takes effect. Otherwise a human edit already in the file is kept.
        if key in OVERRIDES:
            result[key] = OVERRIDES[key]
        else:
            result[key] = existing.get(key) or humanise(key)
    return result


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
        "-- domain_translation key set from the widget labels in\n"
        "-- g2p_register_sections.sql and the values in models/enums.py. A key the\n"
        "-- UI references but this row lacks is rendered raw in the staff portal.\n"
        "--\n"
        "-- core_translation is left empty on purpose: the platform UI ships its own.\n"
        "-- Additional languages are added through the staff portal's language editor.\n"
        'INSERT INTO "public"."registry_languages" ("language_id","language_code","language_label",'
        '"language_flag_base64","is_default","core_translation","domain_translation") VALUES \n'
        + ",\n".join(rows)
        + "\n"
        + 'ON CONFLICT ("language_id") DO NOTHING;\n'
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
