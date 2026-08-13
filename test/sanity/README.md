# Sanity tests — Set 2 (field-specific)

The sanity **harness** and the extension-independent tests (Set 1: smoke plus the
fail-closed negative cases) come from the platform image
`registry-platform/sanity-tests` and run unchanged. This directory holds only the
files that have to know about *this* registry, and the image
(`docker/sanity-tests/Dockerfile`) copies them over the reference registry's
versions at the same paths:

| File | Overlays | What it carries |
|---|---|---|
| `sanity/fixtures.py` | `/app/sanity/fixtures.py` | identifiers and demographics of the injected record |
| `sanity/data_seed.py` | `/app/sanity/data_seed.py` | the SQL that injects it into `g2p_register_persons_with_disability` |
| `tests/test_e2e_dci.py` | `/app/tests/test_e2e_dci.py` | DCI search assertions against our template |
| `tests/test_e2e_change_request.py` | `/app/tests/test_e2e_change_request.py` | change-request → AWE → history, against our tables |

## `fixtures.py` is a contract

The inherited harness imports these symbols **by name**. Change the values
freely; never rename or remove a symbol. That includes the `FARMER_*` names —
they are named for the registry the harness was first written against and mean
"the seeded registrant" here. Renaming them means changing the platform harness,
`conftest.py` and every other registry's overlay in the same commit.

The same applies to the chart: the register id is passed as
`registry.sanity.farmerRegisterId`, not `registerId`.

## What the suite needs

Everything is supplied as env by the chart (`registry.sanity.*`), not baked into
the image — so the same image works against any environment:

| Value | Set to | Why it matters |
|---|---|---|
| `farmerRegisterId` | `a0000000-…-000000000001` | finds the register's AWE policy and raises the CR against it |
| `regType` | `PersonWithDisability` | goes into the DCI search envelope as `reg_type` |
| `searchText` | `SANITY-PWD-0001` | the DCI search is `search_text ILIKE '%…%'` |
| `dataScopes` | `demographic_info` | must be a **top-level key** of `dr_person_to_dci.json.j2` |
| `deniedScopes` | `disability_details` | must also be a real scope, or the clamping test asserts nothing |
| `crTabId` / `crSectionId` | `pwd_person_tab` / `pwd_demographic_details` | a real, editable section, or the CR is rejected |

`test/test_metadata_consistency.py` checks the scopes against the template, since
a scope that names nothing clamps every record to `{}` and the failure looks like
an empty 200 rather than an error.

## Why the record is injected with SQL

Every staff-portal-api register write is a *change request*. Building the fixture
through the API would mean creating and approving a CR before the DCI test could
run, entangling two tests — and the DCI search needs the record in a known,
ACTIVE, already-approved state to be deterministic.

It is injected rather than reusing seeded sample data because sample people only
exist when `dbSeed.loadSampleData=true`, which production turns off. The e2e must
not depend on them.

`search_text` is written explicitly: it is normally populated by SQLAlchemy event
listeners, which do not fire for raw SQL.

## Running it

```bash
# in-cluster, as part of the install
helm upgrade --install dr ./helm/openg2p-disability-registry \
  --set registry.sanity.enabled=true --set registry.sanity.runE2e=true

kubectl -n <namespace> logs job/<release>-sanity
```

`runE2e` must stay **false** in production: the full round-trip needs Partner
Management, Consent Manager, AWE and Keycloak admin, and it writes a test
identity and a test record into the environment.
