import logging

from ._support_base import G2PSupportRegisterDomainServiceBase
from .utils.validations import (
    ensure_end_on_or_after_start,
    ensure_no_duplicate_composite,
    ensure_not_future,
    has_keys,
    parse_date,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceAssistiveTechnology(G2PSupportRegisterDomainServiceBase):
    """DO.DR.07 AssistiveTechnology."""

    search_keys = ["assistive_technology_type", "support_status", "product_identifier"]
    name_keys = ["assistive_technology_type", "support_status"]

    @property
    def support_model(self):
        from ..models.assistive_technology import G2PRegisterAssistiveTechnology

        return G2PRegisterAssistiveTechnology

    async def validate_support_attributes(self, records: list[dict]):
        ensure_no_duplicate_composite(
            records,
            ["assistive_technology_type", "support_status"],
            "Duplicate assistive technology rows with the same type and status are not allowed",
        )
        for record in records:
            if has_keys(record, "provided_on"):
                ensure_not_future(parse_date(record.get("provided_on")), "provided_on")
            # The replacement date is deliberately allowed to be in the past —
            # that is precisely an overdue replacement, which the unmet-need
            # report needs to be able to see.
            if has_keys(record, "provided_on", "expected_replacement_date"):
                ensure_end_on_or_after_start(
                    parse_date(record.get("provided_on")),
                    parse_date(record.get("expected_replacement_date")),
                    start_label="provided_on",
                    end_label="expected_replacement_date",
                )
