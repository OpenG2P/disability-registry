"""Guards over the registry METADATA — the failures that produce no error.

Almost everything this registry does at runtime is driven by seed SQL, and its
characteristic failure mode is silence: a field name that does not match a
column renders as a blank box, a dropdown whose code list is missing renders as
an empty list, a section referenced by no tab simply never appears. None of it
raises. These tests are where that silence gets turned into a build failure.

Stdlib + pytest only, so they run in CI with no database and no cluster.
"""

import ast
import json
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
EXT = REPO / "disability-extension/src/openg2p_registry_disability_extension"
META = EXT / "meta_data"
MODELS = EXT / "register_domain/models"
TEMPLATES = EXT / "templates"


# ── helpers ──────────────────────────────────────────────────────────────────


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


def read(path: pathlib.Path) -> str:
    return path.read_text()


def section_schemas() -> list[dict]:
    text = read(META / "register-metadata/g2p_register_sections.sql")
    return [json.loads(lit) for lit in sql_literals(text) if lit.startswith("{")]


def walk(node, out: list[dict]):
    if isinstance(node, dict):
        if "widget" in node:
            out.append(node)
        for value in node.values():
            walk(value, out)
    elif isinstance(node, list):
        for item in node:
            walk(item, out)


def all_widgets() -> list[dict]:
    widgets: list[dict] = []
    for schema in section_schemas():
        walk(schema, widgets)
    return widgets


def model_columns() -> dict[str, set[str]]:
    """Mixin class name -> declared column names, parsed from the model files.

    Parsed with `ast` rather than imported, because importing the models needs
    SQLAlchemy and registry-core installed — which would make this test only
    runnable inside the built image, i.e. after the mistake has already shipped.
    """
    out: dict[str, set[str]] = {}
    for path in MODELS.glob("*.py"):
        if path.name in {"__init__.py", "enums.py"}:
            continue
        tree = ast.parse(read(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                names = {
                    target.id
                    for stmt in node.body
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
                    for target in [stmt.target]
                }
                if names:
                    out[node.name] = names
    return out


# Columns every register inherits from registry-core (G2PRegister / G2PPerson /
# G2PGeo / G2PIntakeForm). Restated rather than imported for the reason above.
CORE_COLUMNS = {
    # G2PRegister
    "internal_record_id", "functional_record_id", "link_internal_record_id",
    "link_foundational_id", "record_name", "record_image_document_id",
    "created_by", "created_at", "last_approved_at", "last_approved_by",
    "search_text", "record_status", "record_status_reason",
    # G2PPerson
    "foundational_id", "first_name", "middle_name", "last_name", "given_name",
    "prefix", "suffix", "gender", "birth_date", "phone_numbers", "emails",
    "marital_status", "occupation", "income_level", "language_code",
    "education_level", "registration_date",
    # G2PGeo
    "latitude", "longitude", "altitude", "plus_code", "address_line_1",
    "address_line_2", "postal_code", "country_code",
    "geo_lowest_level_value_id", "geo_code_hierarchy_json",
    # intake-form / core extras referenced by UI schemas
    "application_reference", "ideal_score", "records", "rid",
}


def declared_columns() -> set[str]:
    columns = set(CORE_COLUMNS)
    for names in model_columns().values():
        columns |= names
    return columns


# ── tests ────────────────────────────────────────────────────────────────────


def test_every_widget_data_path_names_a_real_column():
    """A widget bound to a non-existent column renders as a permanently blank
    field. Nothing logs, nothing 500s — the operator just cannot enter the data.
    """
    columns = declared_columns()
    bad = []
    for widget in all_widgets():
        path = widget.get("widget-data-path")
        if not isinstance(path, str) or not path:
            continue  # header-section uses a dict of paths; covered below
        leaf = path.split(".")[-1]
        # `<register_id>.records` addresses a child list, not a column.
        if leaf == "records" or leaf.isdigit():
            continue
        # phone_numbers.0.number — the leaf is a JSON key inside a real column.
        parts = path.split(".")
        if len(parts) >= 3 and parts[-3] in columns and parts[-2].isdigit():
            continue
        if leaf not in columns:
            bad.append(f"{widget.get('widget-id')}: {path}")
    assert not bad, (
        "widget-data-path points at columns that do not exist on any model:\n  "
        + "\n  ".join(sorted(bad))
    )


def test_every_table_column_key_names_a_real_column():
    columns = declared_columns()
    bad = []
    for widget in all_widgets():
        for column in widget.get("widget-data-columns") or []:
            key = column.get("column-key")
            if key and key not in columns:
                bad.append(f"{widget.get('widget-id')}: {key}")
    assert not bad, (
        "table column-key values that match no model column:\n  " + "\n  ".join(sorted(bad))
    )


def test_every_dropdown_attribute_has_a_code_list():
    """A `select` bound to an attribute_id with no rows in g2p_attribute_values
    renders as an empty dropdown — the field becomes unfillable, silently."""
    defined = set()
    for name in ("g2p_attributes.sql", "g2p_attributes_defaults.sql"):
        text = read(META / "lookup-data" / name)
        defined |= set(re.findall(r"\('([A-Z0-9_]+)','[A-Z0-9_]+'", text))

    referenced = set()
    for widget in all_widgets():
        source = widget.get("widget-data-source") or {}
        attribute = (source.get("params") or {}).get("attribute_id")
        if attribute:
            referenced.add(attribute)

    missing = referenced - defined
    assert not missing, (
        f"widgets reference attribute_id values with no code list: {sorted(missing)}.\n"
        "Add them to meta_data/lookup-data/ (or ./scripts/generate-code-lists.py "
        "if they are enum-backed)."
    )


def test_code_lists_match_the_enums():
    """The generated code lists must be in step with models/enums.py.

    Delegated to the generator's own --check so there is exactly one definition
    of what "in step" means.
    """
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/generate-code-lists.py"), "--check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_translations_cover_every_ui_key():
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/generate-translations.py"), "--check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_section_is_reachable_from_a_tab():
    """A section on no tab is invisible in the staff portal."""
    section_ids = {schema["section-id"] for schema in section_schemas()}
    tab_sections = read(META / "register-metadata/g2p_register_ui_tab_sections.sql")
    placed = set(re.findall(r"'(pwd_[a-z_]+)'", tab_sections)) & section_ids
    orphans = section_ids - placed
    assert not orphans, f"sections placed on no tab (invisible in the portal): {sorted(orphans)}"


def test_tab_sections_reference_existing_tabs_and_sections():
    section_ids = {schema["section-id"] for schema in section_schemas()}
    tabs = set(re.findall(r"^\('([a-z0-9_]+)'", read(META / "register-metadata/g2p_register_ui_tabs.sql"), re.M))
    rows = re.findall(
        r"\('[^']+','[^']+','([a-z0-9_]+)','([a-z0-9_]+)',\d+\)",
        read(META / "register-metadata/g2p_register_ui_tab_sections.sql"),
    )
    assert rows, "no tab-section rows parsed — the SQL shape changed"
    for tab_id, section_id in rows:
        assert tab_id in tabs, f"tab-section references unknown tab {tab_id}"
        assert section_id in section_ids, f"tab-section references unknown section {section_id}"


def test_register_ids_are_consistent_across_metadata():
    """Register ids are frozen literals repeated across many files; a typo in one
    produces a section attached to a register that does not exist."""
    definitions = read(META / "register-metadata/g2p_register_definitions.sql")
    known = set(re.findall(r"\('([0-9a-f-]{36})','[A-Za-z]+'", definitions))
    assert known, "no register ids parsed from g2p_register_definitions.sql"

    referencing = {
        "g2p_register_sections.sql",
        "g2p_register_schemas.sql",
        "g2p_register_ui_tabs.sql",
        "g2p_intake_form_definitions.sql",
    }
    for name in referencing:
        text = read(META / "register-metadata" / name)
        for uuid_value in set(re.findall(r"'([0-9a-f]{8}-0000-4000-8000-[0-9a-f]{12})'", text)):
            # Intake-form and score ids are not register ids.
            if uuid_value.startswith(("c1000000", "f0000000", "f1000000", "e0000000")):
                continue
            assert uuid_value in known, f"{name} references unknown register id {uuid_value}"


def test_outbound_template_top_level_keys_are_the_consent_scopes():
    """The scopes configured for the sanity suite must exist in the template.

    A consent scope that names no top-level key clamps every record to {} — the
    partner gets a 200 with nothing in it and no error anywhere.
    """
    template = read(TEMPLATES / "dr_person_to_dci.json.j2")
    values = read(REPO / "helm/openg2p-disability-registry/values.yaml")

    scopes: list[str] = []
    for key in ("dataScopes", "deniedScopes"):
        m = re.search(rf"^\s*{key}:\s*\"([^\"]*)\"", values, re.M)
        if m:
            scopes += [s.strip() for s in m.group(1).split(",") if s.strip()]
    assert scopes, "no dataScopes/deniedScopes found in values.yaml"

    for scope in scopes:
        assert re.search(rf'^\s*"{re.escape(scope)}":', template, re.M), (
            f"consent scope '{scope}' is not a top-level key of dr_person_to_dci.json.j2"
        )


def test_awe_policy_keys_match_between_registry_and_awe_seeds():
    """The registry binds a policy by key; AWE creates it by key. A mismatch
    means change requests are raised and never routed for approval."""
    bindings = read(META / "awe-integration/g2p_registry_awe_policy_configurations.sql")
    policies = read(EXT / "awe_meta_data/10_approval_policy.sql")

    bound = set(re.findall(r"'(registry\.[a-z_]+\.[a-z_]+)'", bindings))
    created = set(re.findall(r"'(registry\.[a-z_]+\.[a-z_]+)'", policies))
    assert bound, "no policy keys parsed from the AWE binding SQL"
    missing = bound - created
    assert not missing, f"registry binds AWE policy keys that awe_meta_data never creates: {sorted(missing)}"


def test_seed_sql_is_idempotent():
    """meta_data/ re-runs on every upgrade, so every INSERT needs a conflict
    clause. Without one the second install aborts the whole file — and the
    entrypoint runs psql with ON_ERROR_STOP=0, so it aborts quietly."""
    offenders = []
    for path in sorted(META.rglob("*.sql")):
        text = read(path)
        if "INSERT INTO" not in text:
            continue
        if "ON CONFLICT" not in text.upper():
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, (
        "seed SQL with an INSERT but no ON CONFLICT clause (not re-runnable):\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("name", ["dr_person_to_dci.json.j2", "dci_to_dr_person.json.j2",
                                  "dci_commons_response.json.j2"])
def test_templates_referenced_by_metadata_exist(name):
    documents = read(META / "register-metadata/g2p_registry_documents.sql")
    assert name in documents, (
        f"{name} is not registered in g2p_registry_documents.sql — db-seed would "
        f"upload it to MinIO but nothing would reference it"
    )
    assert (TEMPLATES / name).is_file(), f"{name} is registered in metadata but does not exist"
