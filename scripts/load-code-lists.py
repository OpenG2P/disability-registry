#!/usr/bin/env python3
"""Load this registry's code lists into a running Master Data.

Why this exists
---------------
The staff portal's dropdowns are read from the Master Data Service. The lists
this registry needs belong in a country pack, but until a pack carries them an
environment's Master Data simply does not have them and the dropdowns are empty.
The registry's own db-seed cannot help: registry seeding does not write Master
Data. This script is the manual step in between.

What it does
------------
It adds the lists in master-data/disability/ that the Master Data does NOT
already have. A list that exists, whoever loaded it, is the country's and is
never touched: not its values, not its labels. That is the whole safety rule,
and it is why the plain SQL in meta_data/lookup-data/ must not be run as it is
against a Master Data that already has, say, GENDER.

Two kinds of Master Data are handled, detected from the database:

  catalogue   lists are versioned (g2p_list_versions exists). New lists go in
              through Master Data's own loader, load_geo_pack.load_codelists,
              and are published as version 1 in the domain `disability`. Run
              this inside the openg2p/master-data-db-seed image, which ships
              that loader in /seed.
  plain       lists are rows in g2p_attributes / g2p_attribute_values. New
              lists are inserted directly.

Nothing is saved unless --apply is given: the default is a dry run that does
everything inside a transaction, reports, and rolls back.

Usage
-----
    PGHOST=... PGUSER=master_data_user PGPASSWORD=... \\
        python load-code-lists.py --lists master-data/disability            # dry run
    ... python load-code-lists.py --lists master-data/disability --apply

Connection: PGHOST, PGPORT, PGUSER, PGPASSWORD, and MDS_DB (default master_data).
See master-data/README.md for running it in a cluster.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
import tempfile

DOMAIN = "disability"
ACTOR = "disability-registry-manual-load"


def read_lists(folder: pathlib.Path, only: set[str]) -> dict[str, dict]:
    lists = {}
    for path in sorted(folder.glob("*.json")):
        document = json.loads(path.read_text())
        if only and document["attribute_id"] not in only:
            continue
        lists[document["attribute_id"]] = document
    if not lists:
        raise SystemExit(f"no lists found in {folder}")
    return lists


class NoCommit:
    """A connection whose commit does nothing, so a dry run can be rolled back."""

    def __init__(self, connection):
        self._connection = connection

    def cursor(self, *args, **kwargs):
        return self._connection.cursor(*args, **kwargs)

    def commit(self):
        pass


def load_plain(connection, new: dict[str, dict]) -> None:
    with connection.cursor() as cursor:
        for attribute_id, document in new.items():
            cursor.execute(
                "INSERT INTO g2p_attributes (attribute_id, attribute_code, attribute_display, is_hierarchical) "
                "VALUES (%s, %s, %s, %s)",
                (attribute_id, document.get("attribute_code") or attribute_id, document.get("attribute_display"),
                 bool(document.get("is_hierarchical"))),
            )
            for value in document["values"]:
                cursor.execute(
                    "INSERT INTO g2p_attribute_values "
                    "(value_id, attribute_id, value_code, value_display, parent_value_id, sort_order) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (value["value_id"], attribute_id, value.get("value_code") or value["value_id"],
                     value.get("value_display"), value.get("parent_value_id"), value.get("sort_order")),
                )


def load_catalogue(connection, new: dict[str, dict], apply: bool, loader_dir: str, note: str) -> None:
    sys.path.insert(0, loader_dir)
    try:
        import load_geo_pack as loader  # Master Data's own pack loader
    except ImportError as error:
        raise SystemExit(
            f"this Master Data is the catalogue kind, and its loader was not found in {loader_dir} ({error}). "
            "Run this script inside the openg2p/master-data-db-seed image."
        )
    loader.require_catalogue_schema(connection)
    pack = pathlib.Path(tempfile.mkdtemp(prefix="dr-lists-"))
    try:
        folder = pack / "domains" / DOMAIN
        folder.mkdir(parents=True)
        for attribute_id, document in new.items():
            (folder / f"{attribute_id.lower()}.json").write_text(json.dumps(document))
        arguments = argparse.Namespace(country="n/a", actor=ACTOR, owner_org=None, publish_initial=True, publish=False)
        loader.load_codelists(
            connection if apply else NoCommit(connection), str(pack), {"version": note}, [DOMAIN], arguments,
            loader.ChangeLog(ACTOR),
        )
    finally:
        shutil.rmtree(pack, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--lists", required=True, type=pathlib.Path, help="folder of <list>.json files")
    parser.add_argument("--apply", action="store_true", help="save the changes (default: dry run, rolled back)")
    parser.add_argument("--only", default="", help="comma-separated list ids to consider (default: all)")
    parser.add_argument("--db", default=os.environ.get("MDS_DB", "master_data"))
    parser.add_argument("--loader-dir", default=os.environ.get("MDS_LOADER_DIR", "/seed"),
                        help="where load_geo_pack.py lives (catalogue Master Data only)")
    parser.add_argument("--note", default="Disability Registry lists loaded by hand",
                        help="recorded as the change note of each new list (catalogue Master Data only)")
    args = parser.parse_args()

    import psycopg2

    lists = read_lists(args.lists, {x.strip() for x in args.only.split(",") if x.strip()})
    connection = psycopg2.connect(
        dbname=args.db,
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", ""),
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.g2p_list_versions') IS NOT NULL")
        catalogue = cursor.fetchone()[0]
        cursor.execute("SELECT attribute_id FROM g2p_attributes")
        present = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT count(*) FROM g2p_attribute_values")
        values_before = cursor.fetchone()[0]

    existing = sorted(a for a in lists if a in present)
    new = {a: d for a, d in lists.items() if a not in present}
    print(f"Master Data: {'catalogue (versioned lists)' if catalogue else 'plain tables'}, "
          f"{len(present)} lists, {values_before} values")
    print(f"already there, left untouched ({len(existing)}): {', '.join(existing) or '-'}")
    print(f"to add ({len(new)}): {', '.join(new) or '-'}")
    if not new:
        print("nothing to do")
        return 0

    if catalogue:
        load_catalogue(connection, new, args.apply, args.loader_dir, args.note)
    else:
        load_plain(connection, new)

    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM g2p_attributes")
        lists_after = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM g2p_attribute_values WHERE attribute_id = ANY(%s)", (list(new),))
        added_values = cursor.fetchone()[0]
    expected = sum(len(d["values"]) for d in new.values())
    print(f"after: {lists_after} lists; values in the new lists: {added_values} (expected {expected})")
    if added_values != expected:
        connection.rollback()
        raise SystemExit("value count does not match; rolled back, nothing saved")
    if args.apply:
        connection.commit()
        print("APPLIED")
    else:
        connection.rollback()
        print("DRY RUN: rolled back, nothing was saved. Re-run with --apply to save.")
    connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
