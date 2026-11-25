# OpenG2P Disability Registry

A registry of **persons with disability**, built on the OpenG2P Registry
Platform and modelled on the [SPDCI Disability Registry data
objects](https://standards.spdci.org/standards/dci-standards/wip-disability-registry)
(DO.DR.01 – DO.DR.10).

It is a **single-register, individual-subject** registry: there is no household
or group register. The relationships that matter for disability support —
guardians, primary caregivers, emergency contacts — are recorded as related
persons rather than inferred from co-residence, because the people who matter to
a disability case are frequently not the people someone lives with.

The registry is **country-agnostic**. Geography, code lists and programme names
all come from whatever country pack the environment's Master Data Service holds;
nothing here names a country, an administrative level, or a national programme.

No country pack carries this registry's own lists yet (impairment type, support
status, assistive technology and the rest), so a Master Data has to be given
them: [`master-data/`](master-data/README.md) holds them in pack format, and
`./scripts/load-code-lists.py` adds the ones an environment lacks.

## What it holds

| Register | Mnemonic | SPDCI object |
|---|---|---|
| Person with Disability (master) | `PersonWithDisability` | DO.DR.01 + DO.DR.02 + DO.DR.03 |
| Disability Details | `DisabilityDetail` | DO.DR.04 |
| Human Assistance | `HumanAssistance` | DO.DR.06 |
| Assistive Technology | `AssistiveTechnology` | DO.DR.07 |
| Medical Care | `MedicalCare` | DO.DR.08 |
| Housing Support | `HousingSupport` | DO.DR.09 |
| Animal Assistance | `AnimalAssistance` | DO.DR.10 |
| Related Persons | `RelatedPerson` | DO.DR.02 `related_person` |
| Programme Enrolments | `ProgramEnrolment` | DO.DR.03 `programs_enrolments` |

DO.DR.05 `DisabilitySupport` is a container in the standard, not an entity — it
groups objects 06–10. It is modelled here as the grouping of those five
sub-registers and reappears as one `disability_support` block in the outbound
DCI record.

### The one thing this registry is built to answer

**Who needs support they are not getting, and where are they?**

Every support row carries `support_status`, and the gap between `REQUIRED` and
`RECEIVING`/`RECEIVED` is the unmet need. That single distinction drives the
denormalised `has_unmet_support_need` flag on the person, the `SUPPORT_NEED`
triage score, the headline dashboard, and the map. "Unmet" is defined in exactly
four places and they are kept in step deliberately — see
[`utils/support_summary.py`](disability-extension/src/openg2p_registry_disability_extension/register_domain/services/utils/support_summary.py).

## Speaking the SPDCI standard

Data crosses to and from other systems through two Jinja templates in
`disability-extension/.../templates/`. Everything the standard fixes about that
exchange is handled in one place each:

- **Code lists** (CD.DR.01 – CD.DR.15, CD.COM sex / identifier / relationship):
  one table per list in
  [`register_domain/models/dci_crosswalk.py`](disability-extension/src/openg2p_registry_disability_extension/register_domain/models/dci_crosswalk.py),
  copied into both templates by `./scripts/generate-dci-crosswalk.py`. Inbound
  accepts the standard's label, its numeric code and our enum name; outbound
  emits the standard's label. Unknown values fall back, never guess.
  `test/test_dci_crosswalk.py` renders every standard value through both
  templates and fails the build if one does not round-trip.
- **Record layout** follows DO.DR.03: the DO.DR.02 Member block sits under
  `personal_details`, `disability_support` is a list whose elements each carry
  one `human_assistance`, `age_on_set` is the CD.DR.07 life stage, `UIN` is the
  national ID. The inbound template also still accepts the older flat layout.
- **Disability-specific endpoints** (API.DR.05 – 07:
  `/dci/registry/sync/get-disability-status`, `get-disability-details`,
  `get-disability-support`) are served by this extension from
  `partner_api/dr_controller.py`, attached to the partner API at start-up. They
  reuse the platform's signature and consent checks. The common endpoints
  (search, subscribe, notify, status) stay with the platform.
- **Filtering by location** (API.DR.01 expression search): the person row carries
  `geo_level_1..5_value_id`, derived from the Master Data hierarchy by
  `services/utils/geo_levels.py`, and the chart lists them in
  `REGISTRY_PARTNER_API_DCI_EXPRESSION_ALLOWED_FIELDS`.

Known gap: the platform renders templates without a current date, so CD.DR.14
"Expired" appears in a search response only when the stored status is `EXPIRED`;
the `get-disability-status` endpoint compares `certificate_expiry_date` live.

## Repository layout

```
disability-registry/
├── disability-extension/          the Python package: the domain  (see its README)
├── docker/                        five thin Dockerfiles + the content the images carry
├── helm/openg2p-disability-registry/   values overlay over the platform chart + analytics jobs
├── master-data/                   GENERATED code lists in country-pack format, for Master Data  (see its README)
├── test/                          repo-level guards + the sanity Set-2 tests
├── scripts/                       version pinning, code-list/translation generation and loading, uninstall
├── translation/domain.json        GENERATED — see scripts/generate-translations.py
└── .github/workflows/            declares what to build; the logic is in openg2p-packaging
```

## Working on it

```bash
# repo-level guards — no cluster, no database, run these first
pytest test/test_rp_pin_lockstep.py test/test_metadata_consistency.py

# regenerate after editing models/enums.py or the section metadata
# (translations first: the code lists take their display names from them)
./scripts/generate-translations.py
./scripts/generate-code-lists.py

# give a Master Data the lists it lacks (dry run unless --apply; see master-data/README.md)
./scripts/load-code-lists.py --lists master-data/disability

# move the platform pin (chart + every Dockerfile together)
./scripts/bump-rp-version.sh -n        # preview
./scripts/bump-rp-version.sh <version> # apply

# chart
helm dependency update ./helm/openg2p-disability-registry
helm lint ./helm/openg2p-disability-registry
helm template dr ./helm/openg2p-disability-registry

# images (build context is the repo root)
docker build -f docker/staff-api/Dockerfile -t dr/staff-api:dev .
```

### Rebuilding the dashboard bundle

`files/dr-dashboards.zip` (7 dashboards, 59 charts) is **committed**, as in the
Farmer Registry and NSR — CI packages the chart with no database to read the
reporting views from, and `.Files.Get` cannot reach outside the chart directory,
so building at package time is not an option.

The cost is a binary no review can read. Mitigate it by **rebuilding rather than
hand-editing**, whenever the reporting views change:

```bash
# the builder reads the views' REAL column list, so they must exist somewhere
# reachable — point PGHOST/PGPORT at an installed registry
python docker/dashboards/build_bundle.py \
  --out helm/openg2p-disability-registry/files/dr-dashboards.zip
```

Asset UUIDs come from `uuid5` over stable keys, so re-importing updates the
existing dashboards in place instead of duplicating them.

## Three things that will bite you

These are the failure modes this codebase is shaped around. All three are
**silent** — nothing logs, nothing 500s.

1. **Field names are a four-way contract.** A column is named in `models/`,
   again in the section JSON, again in the DCI templates, again in the reporting
   views. A mismatch gives you a blank field or a missing key, not an error.
   `test/test_metadata_consistency.py` turns each of those into a build failure.

2. **A consent scope that names no top-level key of the outbound template clamps
   every record to `{}`.** The partner gets a 200 with nothing in it. The scopes
   live in `values.yaml` under `registry.sanity.dataScopes`; the guard checks
   them against the template.

3. **Seed SQL re-runs on every upgrade**, and the entrypoint runs `psql` with
   `ON_ERROR_STOP=0` — so an `INSERT` without an `ON CONFLICT` clause aborts its
   file quietly on the second install. There is a guard for that too.

## Documentation

Implementation guidance lives in GitBook, not here:
[Building a Registry](https://docs.openg2p.org/products/registry/registry/developer-zone/building-a-registry).
This README covers only what is specific to this repository.

## Licence

Mozilla Public License 2.0. See [LICENSE](LICENSE).
