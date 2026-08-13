import logging

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import (
    as_int,
    ensure_in_range,
    ensure_no_duplicate_key,
    ensure_not_future,
    has_keys,
    normalized,
    parse_date,
    validate_support_dates,
    validation_error,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceDisabilityDetail(G2PRegisterDomainService):
    """DO.DR.04 DisabilityDetails."""

    async def validate_domain_attributes(self, records: list[dict]):
        ensure_no_duplicate_key(
            records,
            "impairment_type",
            "Duplicate impairment_type entries are not allowed — record one row per impairment",
        )
        self._validate_single_primary_impairment(records)
        for record in records:
            self._validate_age_on_set(record)
            self._validate_assessment_dates(record)
        validate_support_dates(records)

    def _validate_single_primary_impairment(self, records: list[dict]) -> None:
        """At most one impairment may be flagged primary.

        The primary impairment is what drives certificate category and headline
        reporting; two of them means the registry cannot answer its own most
        basic question.
        """
        primary_count = sum(
            1
            for record in records
            if has_keys(record, "is_primary_impairment")
            and normalized(record.get("is_primary_impairment")) in {"TRUE", "1", "YES"}
        )
        if primary_count > 1:
            validation_error("Only one impairment may be marked as the primary impairment")

    def _validate_age_on_set(self, record: dict) -> None:
        if has_keys(record, "age_on_set"):
            ensure_in_range(
                as_int(record.get("age_on_set")), minimum=0, maximum=130, field_label="age_on_set"
            )
        if has_keys(record, "onset_date"):
            ensure_not_future(parse_date(record.get("onset_date")), "onset_date")

    def _validate_assessment_dates(self, record: dict) -> None:
        if has_keys(record, "assessed_on"):
            ensure_not_future(parse_date(record.get("assessed_on")), "assessed_on")

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for disability detail")
        keys = [
            "functional_record_id",
            "impairment_type",
            "impairment_level",
            "impairment_cause",
            "diagnosis_code",
        ]
        return _join(payload, keys, extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for disability detail")
        return _join(payload, ["impairment_type", "impairment_level"], extra)

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
