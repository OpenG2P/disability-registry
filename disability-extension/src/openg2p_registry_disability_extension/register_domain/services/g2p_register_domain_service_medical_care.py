import logging

from ._support_base import G2PSupportRegisterDomainServiceBase
from .utils.validations import (
    as_float,
    ensure_no_duplicate_composite,
    ensure_non_negative,
    has_keys,
)

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceMedicalCare(G2PSupportRegisterDomainServiceBase):
    """DO.DR.08 MedicalCare."""

    search_keys = ["medical_care_type", "support_status", "provider_name"]
    name_keys = ["medical_care_type", "support_status"]

    @property
    def support_model(self):
        from ..models.medical_care import G2PRegisterMedicalCare

        return G2PRegisterMedicalCare

    async def validate_support_attributes(self, records: list[dict]):
        ensure_no_duplicate_composite(
            records,
            ["medical_care_type", "provider_name"],
            "Duplicate medical care rows for the same type and provider are not allowed",
        )
        for record in records:
            if has_keys(record, "monthly_out_of_pocket_cost"):
                # A negative out-of-pocket cost is not a refund, it is a typo —
                # and this column is summed into household cost burden.
                ensure_non_negative(
                    as_float(record.get("monthly_out_of_pocket_cost")),
                    "monthly_out_of_pocket_cost",
                )
