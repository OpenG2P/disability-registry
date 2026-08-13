import logging

from ._support_base import G2PSupportRegisterDomainServiceBase
from .utils.validations import ensure_no_duplicate_composite

_logger = logging.getLogger("g2p-register-domain-service")


class G2PRegisterDomainServiceAnimalAssistance(G2PSupportRegisterDomainServiceBase):
    """DO.DR.10 AnimalAssistance."""

    search_keys = ["animal_assistance_type", "support_status", "certification_reference"]
    name_keys = ["animal_assistance_type", "support_status"]

    @property
    def support_model(self):
        from ..models.animal_assistance import G2PRegisterAnimalAssistance

        return G2PRegisterAnimalAssistance

    async def validate_support_attributes(self, records: list[dict]):
        # Deliberately keyed on the certification, not the type: a person may
        # legitimately have two guide dogs across a handover period, but not two
        # rows for the same certified animal. No check on
        # certification_expiry_date being in the past — an expired certification
        # is exactly the state a renewal programme needs to find.
        ensure_no_duplicate_composite(
            records,
            ["animal_assistance_type", "certification_reference"],
            "Duplicate animal assistance rows for the same certification are not allowed",
        )
