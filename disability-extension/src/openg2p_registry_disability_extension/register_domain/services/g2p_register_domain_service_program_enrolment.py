import logging
from datetime import date

from openg2p_registry_core.services import G2PRegisterDomainService

from .utils.validations import (
    as_float,
    ensure_end_on_or_after_start,
    ensure_non_negative,
    has_keys,
    is_blank,
    normalized,
    parse_date,
    validate_support_dates,
    validation_error,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceProgramEnrolment(G2PRegisterDomainService):
    """DO.DR.03 `programs_enrolments`."""

    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            self._validate_program_name(record)
            self._validate_dates(record)
            self._validate_benefit(record)
        self._validate_no_overlapping_enrolments(records)
        validate_support_dates(records)

    def _validate_program_name(self, record: dict) -> None:
        if not has_keys(record, "program_name"):
            return
        if is_blank(record.get("program_name")):
            validation_error("program_name is required")

    def _validate_dates(self, record: dict) -> None:
        if has_keys(record, "enrolment_start_date", "enrolment_end_date"):
            ensure_end_on_or_after_start(
                parse_date(record.get("enrolment_start_date")),
                parse_date(record.get("enrolment_end_date")),
                start_label="enrolment_start_date",
                end_label="enrolment_end_date",
            )

    def _validate_benefit(self, record: dict) -> None:
        if has_keys(record, "benefit_amount"):
            ensure_non_negative(as_float(record.get("benefit_amount")), "benefit_amount")

    def _validate_no_overlapping_enrolments(self, records: list[dict]) -> None:
        """One programme, one live enrolment at a time.

        Two overlapping enrolments in the same programme means the person is
        double-counted in coverage statistics and potentially double-paid, which
        is the exact failure the DO.DR.03 programme list exists to prevent.
        An open-ended enrolment (no end date) runs to `date.max` for this check.
        """
        seen: list[tuple[str, date, date]] = []
        for record in records:
            if not has_keys(record, "program_name"):
                continue
            program = normalized(record.get("program_name"))
            if not program:
                continue
            start = parse_date(record.get("enrolment_start_date")) or date.min
            end = parse_date(record.get("enrolment_end_date")) or date.max
            for other_program, other_start, other_end in seen:
                if other_program != program:
                    continue
                if start <= other_end and other_start <= end:
                    validation_error(
                        f"Overlapping enrolment periods for programme '{record.get('program_name')}'"
                        " are not allowed"
                    )
            seen.append((program, start, end))

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for program enrolment")
        keys = [
            "functional_record_id",
            "program_name",
            "program_identifier",
            "beneficiary_identifier",
            "enrolment_status",
        ]
        return _join(payload, keys, extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for program enrolment")
        return _join(payload, ["program_name", "enrolment_status"], extra)

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
