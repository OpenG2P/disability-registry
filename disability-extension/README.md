# openg2p-registry-disability-extension

The domain model of the OpenG2P **Disability Registry**, packaged as an
extension to the OpenG2P Registry Platform.

This package carries no service code. It declares the registers, their ORM
models and API schemas, the domain behaviour attached to each, and the seed SQL
that turns them into a working registry — screens, code lists, approval policies
and data-sharing templates. Everything else (the APIs, Keycloak wiring, celery,
db-seed machinery, the sanity harness) comes from the platform images this
extension is installed into.

## Registers

A single top-level register with eight detail tables. There is no group or
household register: the subject of this registry is the individual.

| Register | Mnemonic | SPDCI data object |
|---|---|---|
| Person with Disability | `PersonWithDisability` | DO.DR.01 DRPerson + DO.DR.02 Member + DO.DR.03 PersonwithDisability |
| Disability Details | `DisabilityDetail` | DO.DR.04 |
| Human Assistance | `HumanAssistance` | DO.DR.06 |
| Assistive Technology | `AssistiveTechnology` | DO.DR.07 |
| Medical Care | `MedicalCare` | DO.DR.08 |
| Housing Support | `HousingSupport` | DO.DR.09 |
| Animal Assistance | `AnimalAssistance` | DO.DR.10 |
| Related Persons | `RelatedPerson` | DO.DR.02 `related_person` |
| Programme Enrolments | `ProgramEnrolment` | DO.DR.03 `programs_enrolments` |

DO.DR.05 `DisabilitySupport` is a *container* in the standard rather than an
entity — it groups objects 06 to 10. It is modelled here as the grouping of
those five sub-registers, and reappears as a single `disability_support` block in
the outbound DCI template.

## Layout

```
src/openg2p_registry_disability_extension/
├── app.py                 wires the extension into the platform app
├── config.py              extension settings
├── register_domain/
│   ├── models/            SQLAlchemy ORM — register, history, intake_form per register
│   ├── schemas/           Pydantic API representations
│   ├── services/          per-register domain behaviour (validation, naming, hooks)
│   └── id_generator/      functional-ID affixes
├── meta_data/             seed SQL: registers, UI, code lists, message rules
├── awe_meta_data/         approval-workflow seed SQL
├── templates/             DCI Jinja templates (in and out)
├── score_compute/         the SUPPORT_NEED score
└── ingestion_pipeline/    inbound payload enrichers
```

## Two things worth knowing before editing

**Field names are a four-way contract.** A column exists in `models/`, is named
again in the section JSON in `meta_data/register-metadata/`, again in the DCI
templates, and again in the reporting views. A mismatch produces no error — just
a blank field, an empty dropdown, or a missing key in a shared record.
`test/test_metadata_consistency.py` at the repo root is what turns those silent
failures into build failures; run it after any change here.

**Code lists are generated.** The dropdown values in
`meta_data/lookup-data/*_defaults.sql` are derived from `models/enums.py` by
`./scripts/generate-code-lists.py`. Edit the enum, re-run the script. The same
applies to `translation/domain.json` via `./scripts/generate-translations.py`.

## Installation

The package installs under its **own** import name. It is selected at runtime by
the `REGISTRY_EXTENSION_MODULE` environment variable, which the platform
entrypoints alias into `sys.modules` as `openg2p_registry_extensions`. Do not
alias it yourself, and do not import
`openg2p_registry_disability_extension` from code that the platform resolves
through that alias — the factories deliberately import the alias so this
extension and the platform's reference extension can coexist in one image.

```
pip install ./disability-extension
export REGISTRY_EXTENSION_MODULE=openg2p_registry_disability_extension
```

## Licence

Mozilla Public License 2.0. See [LICENSE](LICENSE).
