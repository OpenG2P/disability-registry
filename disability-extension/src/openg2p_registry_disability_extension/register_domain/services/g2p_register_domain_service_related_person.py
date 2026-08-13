import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import (
    ensure_no_duplicate_composite,
    ensure_not_future,
    has_keys,
    is_blank,
    normalized,
    parse_date,
    validate_support_dates,
    validation_error,
)

_logger = logging.getLogger("g2p-register-domain-service")

_TRUE = {"TRUE", "1", "YES"}


class G2PRegisterDomainServiceRelatedPerson(G2PRegisterDomainService):
    """DO.DR.02 Member `related_person`."""

    async def validate_domain_attributes(self, records: list[dict]):
        ensure_no_duplicate_composite(
            records,
            ["relationship_type", "related_person_identifier"],
            "The same related person cannot be recorded twice with the same relationship",
        )
        self._validate_single_flag(records, "is_primary_caregiver", "primary caregiver")
        self._validate_single_flag(records, "is_legal_guardian", "legal guardian")
        for record in records:
            self._validate_name(record)
            if has_keys(record, "related_person_birth_date"):
                ensure_not_future(
                    parse_date(record.get("related_person_birth_date")),
                    "related_person_birth_date",
                )
        validate_support_dates(records)

    def _validate_single_flag(self, records: list[dict], key: str, label: str) -> None:
        """At most one related person may hold each of these roles.

        Two primary caregivers or two legal guardians is not a richer record, it
        is an unresolved question — and downstream a caregiver allowance would
        have no single payee to resolve to.
        """
        count = sum(
            1
            for record in records
            if has_keys(record, key) and normalized(record.get(key)) in _TRUE
        )
        if count > 1:
            validation_error(f"Only one related person may be marked as the {label}")

    def _validate_name(self, record: dict) -> None:
        if not has_keys(record, "related_person_name"):
            return
        if is_blank(record.get("related_person_name")):
            validation_error("related_person_name is required")

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for related person")
        keys = [
            "functional_record_id",
            "related_person_name",
            "related_person_identifier",
            "relationship_type",
        ]
        return _join(payload, keys, extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for related person")
        return _join(payload, ["related_person_name", "relationship_type"], extra)

    def construct_intake_record_name(self, payload: dict, extra: list[str] = None) -> str:
        return self.construct_record_name(payload, extra)


def _join(payload: dict, keys: list[str], extra: list[str] = None) -> str:
    parts = []
    if extra:
        parts.extend(str(item).strip() for item in extra if str(item).strip())
    parts.extend(
        str(payload.get(key) or "").strip() for key in keys if str(payload.get(key) or "").strip()
    )
    return " ".join(parts).strip()
