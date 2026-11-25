#!/usr/bin/env python3
"""Regenerate the registry's DEFAULT code lists from the domain enums.

Why this exists
---------------
A dropdown in the staff portal is driven by `g2p_attribute_values`; the column
behind it is constrained by a Python enum. When those two drift, the failure is
silent in both directions — a value in the code list but not the enum makes the
field refuse to save, and a value in the enum but not the code list makes it
unreachable from the UI. Neither raises an error anybody sees.

So the code list is DERIVED from the enum rather than maintained beside it. Run
this after changing `register_domain/models/enums.py`;
`test/test_metadata_consistency.py` fails the build if the checked-in files no
longer match.

Where the lists go
------------------
Dropdowns are read from the Master Data Service, not from the registry's own
database, and registry seeding does not write Master Data. So the same lists are
written in the two shapes a Master Data can take them in:

  master-data/disability/<list>.json   the country-pack format (one file per list)
  meta_data/lookup-data/*_defaults.sql rows for a Master Data that still keeps
                                       lists in g2p_attributes / g2p_attribute_values

`scripts/load-code-lists.py` loads them into a running Master Data; see
master-data/README.md. What a value is called on screen comes from
translation/domain.json (scripts/generate-translations.py), so the dropdown and
the rest of the portal use one label. `value_id` equals `value_code`, as in every
list a country pack carries.

These are DEFAULTS. A list the country pack already defines is the country's and
is left alone. Lists with no enum behind them (education, income) are declared in
EXTRA below, because the underlying columns are free text by design — they vary
too much between countries to constrain in code. The three curated lists
(programmes, assessment authorities, data sources) are hand-maintained in
meta_data/lookup-data/g2p_attributes.sql and g2p_attribute_values.sql; this
script only copies them into the pack format.

Usage:  ./scripts/generate-code-lists.py [--check]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
ENUMS = (
    REPO
    / "disability-extension/src/openg2p_registry_disability_extension"
    / "register_domain/models/enums.py"
)
OUT_DIR = (
    REPO
    / "disability-extension/src/openg2p_registry_disability_extension"
    / "meta_data/lookup-data"
)
TRANSLATIONS = REPO / "translation/domain.json"
PACK_DIR = REPO / "master-data/disability"

# Meaning a pack must be able to ask for by role, never by literal (see
# packs/roles.json in openg2p-data). A pack that carries DISABILITY_STATUS must
# say which value means "yes".
ROLES = {("DISABILITY_STATUS", "ASSESSED_DISABLED"): ["disability_yes"]}
DESCRIPTIONS = {
    "DISABILITY_STATUS": (
        "Assessment-based status of a person in a disability registry, as distinct from a "
        "yes/no survey answer. ASSESSED_DISABLED carries the disability_yes role."
    ),
}

# enum class name -> (attribute_id, human display label)
ENUM_TO_ATTRIBUTE = {
    "DisabilityStatusEnum": ("DISABILITY_STATUS", "Disability Status"),
    "DisabilityStatusLevelEnum": ("DISABILITY_STATUS_LEVEL", "Disability Status Level"),
    "SupportNeedsLevelEnum": ("SUPPORT_NEEDS_LEVEL", "Support Needs Level"),
    "LegalCapacityStatusEnum": ("LEGAL_CAPACITY_STATUS", "Legal Capacity Status"),
    "TransportRequirementEnum": ("TRANSPORT_REQUIREMENT", "Transport Requirement"),
    "HousingTypeEnum": ("HOUSING_TYPE", "Housing Type"),
    "CommunicationNeedEnum": ("COMMUNICATION_NEED", "Communication Need"),
    "ImpairmentTypeEnum": ("IMPAIRMENT_TYPE", "Impairment Type"),
    "ImpairmentLevelEnum": ("IMPAIRMENT_LEVEL", "Impairment Level"),
    "ImpairmentCauseEnum": ("IMPAIRMENT_CAUSE", "Impairment Cause"),
    "AgeOnsetBandEnum": ("AGE_ONSET_BAND", "Age of Onset Band"),
    "AssessmentMethodEnum": ("ASSESSMENT_METHOD", "Assessment Method"),
    "SupportStatusEnum": ("SUPPORT_STATUS", "Support Status"),
    "SupportFrequencyEnum": ("SUPPORT_FREQUENCY", "Support Frequency"),
    "ProvisionSourceEnum": ("PROVISION_SOURCE", "Provision Source"),
    "HumanAssistanceTypeEnum": ("HUMAN_ASSISTANCE_TYPE", "Human Assistance Type"),
    "CaregiverRelationshipEnum": ("CAREGIVER_RELATIONSHIP", "Caregiver Relationship"),
    "AssistiveTechnologyTypeEnum": ("ASSISTIVE_TECHNOLOGY_TYPE", "Assistive Technology Type"),
    "MedicalCareTypeEnum": ("MEDICAL_CARE_TYPE", "Medical Care Type"),
    "HousingSupportTypeEnum": ("HOUSING_SUPPORT_TYPE", "Housing Support Type"),
    "AnimalAssistanceTypeEnum": ("ANIMAL_ASSISTANCE_TYPE", "Animal Assistance Type"),
    "RelationshipTypeEnum": ("RELATIONSHIP_TYPE", "Relationship Type"),
    "EmploymentStatusEnum": ("EMPLOYMENT_STATUS", "Employment Status"),
    "PreferredContactMethodEnum": ("PREFERRED_CONTACT_METHOD", "Preferred Contact Method"),
    "VerificationStatusEnum": ("VERIFICATION_STATUS", "Verification Status"),
    "IdentityEvidenceTypeEnum": ("IDENTITY_EVIDENCE_TYPE", "Identity Evidence Type"),
    "RegistrationChannelEnum": ("REGISTRATION_CHANNEL", "Registration Channel"),
    "ProgramEnrolmentStatusEnum": ("PROGRAM_ENROLMENT_STATUS", "Programme Enrolment Status"),
}

# Lists with no enum behind them. GENDER and MARITAL_STATUS mirror registry-core's
# own GenderEnum / MaritalStatusEnum — restated rather than imported so this
# script needs nothing installed to run.
EXTRA: dict[str, tuple[str, list[str]]] = {
    "GENDER": ("Gender", ["MALE", "FEMALE", "OTHERS", "UNKNOWN"]),
    "MARITAL_STATUS": (
        "Marital Status",
        ["SINGLE", "MARRIED", "DIVORCED", "WIDOWED", "SEPARATED", "UNKNOWN"],
    ),
    "EDUCATION_LEVEL": (
        "Education Level",
        [
            "NONE",
            "PRE_PRIMARY",
            "PRIMARY",
            "LOWER_SECONDARY",
            "UPPER_SECONDARY",
            "POST_SECONDARY",
            "TERTIARY",
            "SPECIAL_EDUCATION",
            "VOCATIONAL",
            "UNKNOWN",
        ],
    ),
    "INCOME_LEVEL": (
        "Income Level",
        ["NONE", "LOW", "LOWER_MIDDLE", "MIDDLE", "UPPER_MIDDLE", "HIGH", "UNKNOWN"],
    ),
}


def load_enums():
    spec = importlib.util.spec_from_file_location("dr_enums", ENUMS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect() -> dict[str, tuple[str, list[str]]]:
    module = load_enums()
    lists: dict[str, tuple[str, list[str]]] = {}
    for class_name, (attribute_id, display) in ENUM_TO_ATTRIBUTE.items():
        enum_cls = getattr(module, class_name, None)
        if enum_cls is None:
            raise SystemExit(f"enums.py no longer defines {class_name}")
        lists[attribute_id] = (display, [member.value for member in enum_cls])
    lists.update(EXTRA)
    return dict(sorted(lists.items()))


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sentence(text: str) -> str:
    """'Age of Onset Band' -> 'Age of onset band', the case country packs use."""
    return text[:1].upper() + text[1:].lower()


def value_labels() -> dict[str, str]:
    return json.loads(TRANSLATIONS.read_text()) if TRANSLATIONS.exists() else {}


def label_of(code: str, labels: dict[str, str]) -> str:
    return labels.get(code) or sentence(code.replace("_", " "))


HEADER = """-- Default values for this registry's code lists — GENERATED, do not hand-edit.
--
-- Regenerate with ./scripts/generate-code-lists.py after changing
-- register_domain/models/enums.py. test/test_metadata_consistency.py fails the
-- build if this file and the enums disagree.
--
-- These rows are for a Master Data that keeps lists in g2p_attributes /
-- g2p_attribute_values. The registry's own database has no such tables, so the
-- db-seed job cannot load them; scripts/load-code-lists.py does, and adds only
-- lists the Master Data does not already have. master-data/disability/ holds the
-- same lists in country-pack format.
--
-- These are DEFAULTS, not a definition: a list the country pack also defines is
-- the country's, and an admin can edit any of them in Master Data.

"""


def render(lists: dict[str, tuple[str, list[str]]], labels: dict[str, str]) -> tuple[str, str]:
    attr_rows = [
        f"({sql_quote(a)},{sql_quote(a)},{sql_quote(sentence(display))},'FALSE')"
        for a, (display, _) in lists.items()
    ]
    attributes_sql = (
        HEADER
        + 'INSERT INTO "public"."g2p_attributes" '
        '("attribute_id","attribute_code","attribute_display","is_hierarchical") VALUES \n'
        + ",\n".join(attr_rows)
        + "\nON CONFLICT (attribute_id) DO NOTHING;\n"
    )

    value_rows = []
    for attribute_id, (_display, values) in lists.items():
        for order, value in enumerate(values, start=1):
            value_rows.append(
                f"({sql_quote(value)},{sql_quote(attribute_id)},{sql_quote(value)},"
                f"{sql_quote(label_of(value, labels))},NULL,{order})"
            )
    # Untargeted: Master Data keys a value on (value_id, attribute_id), so the
    # same code may appear in several lists (OTHER, UNKNOWN).
    values_sql = (
        HEADER
        + 'INSERT INTO "public"."g2p_attribute_values" '
        '("value_id","attribute_id","value_code","value_display","parent_value_id","sort_order") VALUES \n'
        + ",\n".join(value_rows)
        + "\nON CONFLICT DO NOTHING;\n"
    )
    return attributes_sql, values_sql


_ROW = re.compile(r"^\((.*)\),?\s*$", re.M)
_FIELD = re.compile(r"'((?:[^']|'')*)'|(NULL)|(\d+)")


def _sql_rows(path: pathlib.Path) -> list[list]:
    rows = []
    for match in _ROW.finditer(path.read_text()):
        fields = []
        for text, null, number in _FIELD.findall(match.group(1)):
            fields.append(None if null else int(number) if number else text.replace("''", "'"))
        rows.append(fields)
    return rows


def curated() -> dict[str, dict]:
    """The hand-maintained lists, read back from their SQL."""
    lists = {
        row[0]: {"display": row[2], "values": []}
        for row in _sql_rows(OUT_DIR / "g2p_attributes.sql")
    }
    for value_id, attribute_id, code, display, _parent, order in _sql_rows(OUT_DIR / "g2p_attribute_values.sql"):
        lists[attribute_id]["values"].append((order, value_id, code, display))
    return lists


def pack_documents(lists: dict[str, tuple[str, list[str]]], labels: dict[str, str]) -> dict[str, dict]:
    """attribute_id -> the list as a country pack writes it."""
    documents = {}
    for attribute_id, (display, values) in lists.items():
        documents[attribute_id] = (
            sentence(display),
            [(order, code, code, label_of(code, labels)) for order, code in enumerate(values, start=1)],
        )
    for attribute_id, entry in curated().items():
        documents[attribute_id] = (sentence(entry["display"]), sorted(entry["values"]))

    rendered = {}
    for attribute_id, (display, values) in sorted(documents.items()):
        document: dict = {
            "attribute_id": attribute_id,
            "attribute_code": attribute_id,
            "attribute_display": display,
        }
        if attribute_id in DESCRIPTIONS:
            document["description"] = DESCRIPTIONS[attribute_id]
        document["is_hierarchical"] = False
        document["values"] = []
        for order, value_id, code, value_display in values:
            value: dict = {
                "value_id": value_id,
                "value_code": code,
                "value_display": value_display,
                "sort_order": order,
            }
            if (attribute_id, code) in ROLES:
                value["roles"] = ROLES[(attribute_id, code)]
            value["display_i18n"] = {}
            document["values"].append(value)
        rendered[attribute_id] = document
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if the checked-in files are stale"
    )
    args = parser.parse_args()

    lists = collect()
    labels = value_labels()
    attributes_sql, values_sql = render(lists, labels)
    documents = pack_documents(lists, labels)
    targets = {
        OUT_DIR / "g2p_attributes_defaults.sql": attributes_sql,
        OUT_DIR / "g2p_attribute_values_defaults.sql": values_sql,
    }
    for attribute_id, document in documents.items():
        targets[PACK_DIR / f"{attribute_id.lower()}.json"] = (
            json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        )

    stale = [p for p, content in targets.items() if not p.exists() or p.read_text() != content]
    # A list that was renamed or dropped must not linger in the pack folder.
    stray = sorted(p for p in PACK_DIR.glob("*.json") if p not in targets) if PACK_DIR.is_dir() else []
    if args.check:
        if stale or stray:
            for path in stale:
                print(f"STALE: {path.relative_to(REPO)}", file=sys.stderr)
            for path in stray:
                print(f"STRAY: {path.relative_to(REPO)}", file=sys.stderr)
            print("\nRun ./scripts/generate-code-lists.py to regenerate.", file=sys.stderr)
            return 1
        print(f"code lists up to date ({len(lists)} generated, {len(documents)} in pack format)")
        return 0

    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in targets.items():
        path.write_text(content)
    for path in stray:
        path.unlink()
    total = sum(len(values) for _display, values in lists.values())
    print(f"wrote {len(lists)} attributes / {total} values to {OUT_DIR.relative_to(REPO)}")
    print(f"wrote {len(documents)} lists to {PACK_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
