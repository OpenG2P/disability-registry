import logging

from ._support_base import G2PSupportRegisterDomainServiceBase
from .utils.validations import (
    as_float,
    ensure_no_duplicate_composite,
    ensure_non_negative,
    ensure_not_future,
    has_keys,
    parse_date,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceHousingSupport(G2PSupportRegisterDomainServiceBase):
    """DO.DR.09 HousingSupport."""

    search_keys = ["housing_support_type", "support_status", "provider_name"]
    name_keys = ["housing_support_type", "support_status"]

    @property
    def support_model(self):
        from ..models.housing_support import G2PRegisterHousingSupport

        return G2PRegisterHousingSupport

    async def validate_support_attributes(self, records: list[dict]):
        ensure_no_duplicate_composite(
            records,
            ["housing_support_type", "support_status"],
            "Duplicate housing support rows with the same type and status are not allowed",
        )
        for record in records:
            if has_keys(record, "completed_on"):
                ensure_not_future(parse_date(record.get("completed_on")), "completed_on")
            if has_keys(record, "estimated_cost"):
                ensure_non_negative(as_float(record.get("estimated_cost")), "estimated_cost")
