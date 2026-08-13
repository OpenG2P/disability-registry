"""Shared validation and coercion helpers for the Disability Registry services.

Change-request payloads are PARTIAL: the staff portal sends only the fields the
operator touched. Every check here is therefore gated on `has_keys(...)` — a
validator that fires on an absent key rejects edits to unrelated fields, which is
the single most common way domain validation breaks a registry.
"""

from datetime import date, datetime

from openg2p_registry_core.errors import G2PRegistryErrorCodes, G2PRegistryException


def validation_error(message: str) -> None:
    raise G2PRegistryException(
        code=G2PRegistryErrorCodes.REQUEST_VALIDATION_ERROR.value[1],
        message=message,
    )


def has_keys(record: dict, *keys: str) -> bool:
    return all(key in record for key in keys)


def parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def as_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def as_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_bool(value) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return bool(value)


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def normalized(value) -> str:
    return str(value).strip().upper() if value is not None else ""


def ensure_no_duplicate_key(records: list[dict], key: str, message: str) -> None:
    seen: set[str] = set()
    for record in records:
        if not has_keys(record, key):
            continue
        value = record.get(key)
        if is_blank(value):
            continue
        marker = normalized(value)
        if marker in seen:
            validation_error(message)
        seen.add(marker)


def ensure_no_duplicate_composite(records: list[dict], keys: list[str], message: str) -> None:
    """Reject two rows that agree on every key in `keys`.

    Used where the natural key is a pair rather than a single column — the same
    assistive product recorded twice with the same status, for instance.
    """
    seen: set[tuple[str, ...]] = set()
    for record in records:
        if not has_keys(record, *keys):
            continue
        marker = tuple(normalized(record.get(key)) for key in keys)
        if any(part == "" for part in marker):
            continue
        if marker in seen:
            validation_error(message)
        seen.add(marker)


def ensure_end_on_or_after_start(
    start: date | None,
    end: date | None,
    *,
    start_label: str,
    end_label: str,
) -> None:
    if start is None or end is None:
        return
    if end < start:
        validation_error(f"{end_label} must be on or after {start_label}")


def ensure_not_future(value: date | None, field_label: str) -> None:
    if value is None:
        return
    if value > date.today():
        validation_error(f"{field_label} must not be in the future")


def ensure_in_range(
    value: int | float | None,
    *,
    minimum: int | float,
    maximum: int | float,
    field_label: str,
) -> None:
    if value is None:
        return
    if value < minimum or value > maximum:
        validation_error(f"{field_label} must be between {minimum} and {maximum}")


def ensure_non_negative(value: int | float | None, field_label: str) -> None:
    if value is None:
        return
    if value < 0:
        validation_error(f"{field_label} must not be negative")


def validate_support_dates(records: list[dict]) -> None:
    """`registration_date` / `last_updated` are common to every support register.

    Neither may be in the future, and an update cannot predate the registration
    that it updates.
    """
    for record in records:
        registration_date = (
            parse_date(record.get("registration_date"))
            if has_keys(record, "registration_date")
            else None
        )
        last_updated = (
            parse_date(record.get("last_updated")) if has_keys(record, "last_updated") else None
        )
        ensure_not_future(registration_date, "registration_date")
        ensure_not_future(last_updated, "last_updated")
        ensure_end_on_or_after_start(
            registration_date,
            last_updated,
            start_label="registration_date",
            end_label="last_updated",
        )
