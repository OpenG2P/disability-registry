import logging

from ._support_base import G2PSupportRegisterDomainServiceBase
from .utils.validations import (
    as_int,
    ensure_in_range,
    ensure_no_duplicate_composite,
    has_keys,
    is_blank,
    normalized,
    validation_error,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceHumanAssistance(G2PSupportRegisterDomainServiceBase):
    """DO.DR.06 HumanAssistance."""

    search_keys = [
        "assistance_type",
        "support_status",
        "caregiver_name",
        "caregiver_identifier",
    ]
    name_keys = ["assistance_type", "support_status"]

    @property
    def support_model(self):
        from ..models.human_assistance import G2PRegisterHumanAssistance

        return G2PRegisterHumanAssistance

    async def validate_support_attributes(self, records: list[dict]):
        ensure_no_duplicate_composite(
            records,
            ["assistance_type", "caregiver_identifier"],
            "The same caregiver cannot be recorded twice for the same assistance_type",
        )
        for record in records:
            self._validate_hours(record)
            self._validate_caregiver(record)

    def _validate_hours(self, record: dict) -> None:
        if not has_keys(record, "hours_per_week"):
            return
        # 168 = hours in a week. Above that is a data-entry error, and it matters:
        # caregiver hours drive caregiver-allowance amounts in most schemes.
        ensure_in_range(
            as_int(record.get("hours_per_week")),
            minimum=0,
            maximum=168,
            field_label="hours_per_week",
        )

    def _validate_caregiver(self, record: dict) -> None:
        """A caregiver who is being received from must be identified.

        Only checked when the payload carries both keys, so editing the status
        alone on a row that already names a caregiver still works.
        """
        if not has_keys(record, "support_status", "caregiver_name"):
            return
        if normalized(record.get("support_status")) not in {"RECEIVING", "RECEIVED"}:
            return
        if is_blank(record.get("caregiver_name")):
            validation_error(
                "caregiver_name is required when human assistance is being received"
            )
