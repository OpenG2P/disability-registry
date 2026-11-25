# Code lists for Master Data

The staff portal's dropdowns are read from the **Master Data Service**, not from
the registry's own database. This folder holds the lists this registry needs, in
the format Master Data takes them in.

```
disability/<list>.json    one file per list, in country-pack format (35 lists)
```

The files are **generated** by `./scripts/generate-code-lists.py` from
`register_domain/models/enums.py` (codes and order) and `translation/domain.json`
(what each value is called). Do not edit them by hand; edit the enum or the
translation and regenerate. `./scripts/generate-code-lists.py --check` fails the
build when they are stale.

## Why they are here and not in the seed

Registry seeding does not write Master Data, and the registry's database has no
list tables, so the db-seed job cannot load these. `meta_data/lookup-data/*.sql`
carries the same lists as SQL rows and still fails on every install with
`relation "g2p_attribute_values" does not exist`; that is expected until those
files are taken out of the seed path.

The permanent home is the country pack: a `domains/disability/` folder in each
pack of [OpenG2P/openg2p-data](https://github.com/OpenG2P/openg2p-data), loaded
when the Master Data chart names the domain
(`geoSeed.domains: [agriculture, disability]`). The files here are already in
that format. A pack takes only the lists it does not already define, because a
list id is unique within a pack.

Until a pack carries them, an environment's Master Data has to be given the lists
by hand.

## Loading them by hand

`scripts/load-code-lists.py` adds the lists a Master Data **does not already
have**. A list that exists is the country's and is never touched. It is a dry run
unless `--apply` is given.

It needs to run where the Master Data database is reachable, with that database's
user. Both kinds of Master Data are handled:

**Catalogue Master Data** (lists are versioned; `/catalogue/...` API). Run it in
a pod from the `openg2p/master-data-db-seed` image of the same version as the
environment's Master Data, which ships Master Data's own loader in `/seed`. New
lists are published as version 1 in the domain `disability`.

**Plain-table Master Data** (older; lists are rows in `g2p_attributes` and
`g2p_attribute_values`). Any image with Python and `psycopg2` will do; the
registry's own db-seed image has both.

```bash
# 1. a short-lived pod with the Master Data database credentials as PG* variables
#    (secret names differ by Master Data version: master-data-db / master-data-db-user)
# 2. copy the lists and the script in
tar czf - -C master-data disability -C ../scripts load-code-lists.py \
  | kubectl -n <ns> exec -i <pod> -- python -c \
    "import sys, tarfile; tarfile.open(fileobj=sys.stdin.buffer, mode='r|gz').extractall('/tmp/dr')"
# 3. look first, then save
kubectl -n <ns> exec <pod> -- python /tmp/dr/load-code-lists.py --lists /tmp/dr/disability
kubectl -n <ns> exec <pod> -- python /tmp/dr/load-code-lists.py --lists /tmp/dr/disability --apply
```

Do **not** run `meta_data/lookup-data/*.sql` as it stands against a Master Data
that already has some of these lists: it would add this registry's values into
the country's `GENDER` or `EDUCATION_LEVEL`.

Undo: in a plain-table Master Data, delete the added list ids from both tables.
In a catalogue Master Data a published version is permanent; retire the list
there instead.

## Loaded by hand so far

| Environment | Master Data | Date | Added | Left as the country's |
|---|---|---|---|---|
| `qa` | plain tables (1.1.4), Kamuntu pack | 2026-11-25 | 32 lists, 273 values | `GENDER`, `MARITAL_STATUS`, `EDUCATION_LEVEL` |
| `dev` | catalogue (0.0.0-develop.118), Ethiopia pack | 2026-11-25 | 26 lists, 231 values | those three, plus `DISABILITY_STATUS`, `EMPLOYMENT_STATUS`, `IDENTITY_EVIDENCE_TYPE`, `PREFERRED_CONTACT_METHOD`, `PROGRAM_NAME`, `VERIFICATION_STATUS` |

The display names corrected alongside (13 labels such as `SMS`, `NGO`,
`ICF based`; see `OVERRIDES` in `scripts/generate-translations.py`) were also
written into each of those registries' English language row on 2026-11-25. A
fresh install gets them from `g2p_registry_languages.sql`; an upgrade does not,
because that seed never overwrites an existing row.

## Where a country's list and the registry disagree

The registry checks most fields against its own enums when a record is saved, so
a country list is only safe where its codes are ones the registry knows. Known
differences:

| List | Country pack | Registry | Effect |
|---|---|---|---|
| `GENDER` | `OTHER` | `OTHERS` | the dropdown offers a value the registry does not know |
| `DISABILITY_STATUS` (Ethiopia) | `YES`, `NO`, `UNKNOWN` | `ASSESSED_DISABLED`, `PENDING_ASSESSMENT`, `EXPIRED`, ... | the registry's statuses are not offered; records hold values the list lacks |
| `EMPLOYMENT_STATUS` (Ethiopia) | six values, with `UNEMPLOYED` | ten values, with `UNEMPLOYED_SEEKING` / `UNEMPLOYED_NOT_SEEKING` | records hold values the list lacks |
| `PROGRAM_NAME` (Ethiopia) | national programmes | generic disability programmes | sample records name programmes the list lacks |

These need a decision each (a second list id, or a change to the country's
list); nothing in this folder settles them.
