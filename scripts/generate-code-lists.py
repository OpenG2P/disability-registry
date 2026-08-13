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
this after changing `register_domain/models/enums.py`; `test/test_enum_values.py`
fails the build if the checked-in SQL no longer matches.

These are DEFAULTS. `load_attributes_from_mds` replaces any list a country pack
also defines, and an administrator can edit them in the staff portal. Lists with
no enum behind them (education, income) are declared in EXTRA below, because the
underlying columns are free text by design — they vary too much between countries
to constrain in code.

Usage:  ./scripts/generate-code-lists.py [--check]
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
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


HEADER = """-- Default values for this registry's code lists — GENERATED, do not hand-edit.
--
-- Regenerate with ./scripts/generate-code-lists.py after changing
-- register_domain/models/enums.py. test/test_enum_values.py fails the build if
-- this file and the enums disagree.
--
-- These are DEFAULTS, not a definition: load_attributes_from_mds replaces any
-- list the country pack also defines, and an admin can edit them in the staff
-- portal. A deployment with no country pack gets exactly these.

"""


def render(lists: dict[str, tuple[str, list[str]]]) -> tuple[str, str]:
    attr_rows = [
        f"({sql_quote(a)},{sql_quote(a)},{sql_quote(display)},'FALSE')"
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
            value_id = f"{attribute_id}:{value}"
            value_rows.append(
                f"({sql_quote(value_id)},{sql_quote(attribute_id)},{sql_quote(value)},"
                f"{sql_quote(value)},NULL,{order})"
            )
    values_sql = (
        HEADER
        + 'INSERT INTO "public"."g2p_attribute_values" '
        '("value_id","attribute_id","value_code","value_display","parent_value_id","sort_order") VALUES \n'
        + ",\n".join(value_rows)
        + "\nON CONFLICT (value_id) DO NOTHING;\n"
    )
    return attributes_sql, values_sql


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if the checked-in files are stale"
    )
    args = parser.parse_args()

    lists = collect()
    attributes_sql, values_sql = render(lists)
    targets = {
        OUT_DIR / "g2p_attributes_defaults.sql": attributes_sql,
        OUT_DIR / "g2p_attribute_values_defaults.sql": values_sql,
    }

    stale = [p for p, content in targets.items() if not p.exists() or p.read_text() != content]
    if args.check:
        if stale:
            for path in stale:
                print(f"STALE: {path.relative_to(REPO)}", file=sys.stderr)
            print("\nRun ./scripts/generate-code-lists.py to regenerate.", file=sys.stderr)
            return 1
        print(f"code lists up to date ({len(lists)} attributes)")
        return 0

    for path, content in targets.items():
        path.write_text(content)
    total = sum(len(values) for _display, values in lists.values())
    print(f"wrote {len(lists)} attributes / {total} values to {OUT_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
