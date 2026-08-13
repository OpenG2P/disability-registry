import logging
from datetime import date

from openg2p_registry_core.models import G2PRegisterChangeRequest
from openg2p_registry_core.services import G2PRegisterDomainService
from sqlalchemy.ext.asyncio import AsyncSession

from .utils.support_summary import recompute_support_summary
from .utils.validations import (
    as_int,
    ensure_end_on_or_after_start,
    ensure_in_range,
    ensure_not_future,
    has_keys,
    is_blank,
    normalized,
    parse_date,
    validation_error,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServicePersonWithDisability(G2PRegisterDomainService):
    """Domain behaviour for the master PersonWithDisability register."""

    async def validate_domain_attributes(self, records: list[dict]):
        for record in records:
            self._validate_names(record)
            self._validate_birth_date(record)
            self._validate_death_date(record)
            self._validate_estimated_age(record)
            self._validate_certificate_dates(record)
            self._validate_assessment_consistency(record)

    # ── field-level checks ───────────────────────────────────────────────────

    def _validate_names(self, record: dict) -> None:
        if not has_keys(record, "first_name"):
            return
        if is_blank(record.get("first_name")):
            validation_error("first_name is required")

    def _validate_birth_date(self, record: dict) -> None:
        if not has_keys(record, "birth_date"):
            return
        ensure_not_future(parse_date(record.get("birth_date")), "birth_date")

    def _validate_death_date(self, record: dict) -> None:
        if not has_keys(record, "death_date"):
            return
        death_date = parse_date(record.get("death_date"))
        ensure_not_future(death_date, "death_date")
        if has_keys(record, "birth_date"):
            ensure_end_on_or_after_start(
                parse_date(record.get("birth_date")),
                death_date,
                start_label="birth_date",
                end_label="death_date",
            )

    def _validate_estimated_age(self, record: dict) -> None:
        if not has_keys(record, "estimated_age"):
            return
        ensure_in_range(as_int(record.get("estimated_age")), minimum=0, maximum=130,
                        field_label="estimated_age")
        if not has_keys(record, "birth_date"):
            return
        birth_date = parse_date(record.get("birth_date"))
        estimated_age = as_int(record.get("estimated_age"))
        if birth_date is None or estimated_age is None:
            return
        computed_age = self._calculate_age(birth_date)
        if computed_age is not None and abs(estimated_age - computed_age) > 1:
            validation_error("estimated_age must be consistent with birth_date within one year")

    def _validate_certificate_dates(self, record: dict) -> None:
        """A certificate cannot expire before it was issued, and an assessment
        cannot be dated in the future. Expiry itself MAY be in the past — that is
        a lapsed certificate, which the registry must be able to represent."""
        if has_keys(record, "assessment_date"):
            ensure_not_future(parse_date(record.get("assessment_date")), "assessment_date")
        if has_keys(record, "certificate_issue_date"):
            ensure_not_future(
                parse_date(record.get("certificate_issue_date")), "certificate_issue_date"
            )
        if has_keys(record, "certificate_issue_date", "certificate_expiry_date"):
            ensure_end_on_or_after_start(
                parse_date(record.get("certificate_issue_date")),
                parse_date(record.get("certificate_expiry_date")),
                start_label="certificate_issue_date",
                end_label="certificate_expiry_date",
            )
        if has_keys(record, "assessment_date", "certificate_issue_date"):
            ensure_end_on_or_after_start(
                parse_date(record.get("assessment_date")),
                parse_date(record.get("certificate_issue_date")),
                start_label="assessment_date",
                end_label="certificate_issue_date",
            )

    def _validate_assessment_consistency(self, record: dict) -> None:
        """An assessed status must be backed by an assessment date.

        Only enforced when the payload carries BOTH keys — a change request that
        edits the status alone leaves the existing assessment_date in place, and
        rejecting it here would make the field uneditable.
        """
        if not has_keys(record, "disability_status", "assessment_date"):
            return
        status = normalized(record.get("disability_status"))
        if status not in {"ASSESSED_DISABLED", "ASSESSED_NOT_DISABLED"}:
            return
        if parse_date(record.get("assessment_date")) is None:
            validation_error(
                "assessment_date is required when disability_status is an assessed outcome"
            )

    # ── record naming and search ─────────────────────────────────────────────

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing search text for person with disability")

        keys = [
            "functional_record_id",
            "first_name",
            "middle_name",
            "last_name",
            "given_name",
            "full_name",
            "alias_names",
            "foundational_id",
            "foundational_id_masked",
            "disability_certificate_number",
            "birth_date",
            "plus_code",
            "address_line_1",
            "address_line_2",
            "postal_code",
        ]
        search_text = []
        if extra:
            search_text.extend(str(value).strip() for value in extra if str(value).strip())
        search_text.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(search_text).strip()

    def construct_intake_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing intake record name for person with disability")

        keys = ["first_name", "last_name", "application_reference"]
        return self._join(payload, keys, extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        _logger.info("Constructing record name for person with disability")

        keys = ["first_name", "last_name"]
        return self._join(payload, keys, extra)

    @staticmethod
    def _join(payload: dict, keys: list[str], extra: list[str] = None) -> str:
        parts = []
        if extra:
            parts.extend(str(item).strip() for item in extra if str(item).strip())
        parts.extend(
            str(payload.get(key) or "").strip()
            for key in keys
            if str(payload.get(key) or "").strip()
        )
        return " ".join(parts).strip()

    # ── lifecycle hooks ──────────────────────────────────────────────────────

    async def post_ingest(self, register_id: str, register_row, session: AsyncSession):
        """A person ingested with support rows needs its summary built once."""
        internal_record_id = getattr(register_row, "internal_record_id", None)
        if internal_record_id:
            await recompute_support_summary(session, internal_record_id)

    async def post_approve(self, change_request: G2PRegisterChangeRequest, session: AsyncSession):
        """Edits to the person can change nothing about support rows, but an
        approval is the cheapest reliable point at which to reconcile a summary
        that drifted — for instance after a bulk import that bypassed the hooks."""
        await recompute_support_summary(session, change_request.internal_record_id)

    @staticmethod
    def _calculate_age(birth_date: date) -> int | None:
        if birth_date is None:
            return None
        today = date.today()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
