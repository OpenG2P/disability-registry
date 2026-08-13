"""Shared behaviour for the five DO.DR.05 DisabilitySupport sub-registers.

All of HumanAssistance, AssistiveTechnology, MedicalCare, HousingSupport and
AnimalAssistance carry `support_status` + `registration_date` + `last_updated`
and all of them feed the person's unmet-need summary. That common part lives
here so the five concrete services differ only where the domain differs.

This is a plain base class, NOT a registered service: the factory resolves
`G2PRegisterDomainService{Mnemonic}` by name, so only the concrete subclasses are
ever instantiated for a register.
"""

import logging

from openg2p_registry_core.models import G2PRegisterChangeRequest
from openg2p_registry_core.services import G2PRegisterDomainService
from sqlalchemy.ext.asyncio import AsyncSession

from .utils.support_summary import recompute_support_summary
from .utils.validations import validate_support_dates

_logger = logging.getLogger("g2p-register-domain-service")


class G2PSupportRegisterDomainServiceBase(G2PRegisterDomainService):
    #: ORM model for this support register — set by each subclass so the base
    #: can resolve a change request back to the person it belongs to.
    support_model = None

    #: Field names that make up search_text / record_name for this register.
    search_keys: list[str] = []
    name_keys: list[str] = []

    async def validate_domain_attributes(self, records: list[dict]):
        validate_support_dates(records)
        await self.validate_support_attributes(records)

    async def validate_support_attributes(self, records: list[dict]):
        """Override for register-specific rules. Default: nothing extra."""

    # ── summary maintenance ──────────────────────────────────────────────────

    async def post_ingest(self, register_id: str, register_row, session: AsyncSession):
        await recompute_support_summary(
            session, getattr(register_row, "link_internal_record_id", None)
        )

    async def post_approve(self, change_request: G2PRegisterChangeRequest, session: AsyncSession):
        """The change request names the SUPPORT row; the summary lives on its
        parent, so resolve the link before recomputing."""
        if self.support_model is None:
            return
        row = await session.get(self.support_model, change_request.internal_record_id)
        if row is None:
            return
        await recompute_support_summary(session, row.link_internal_record_id)

    # ── naming ───────────────────────────────────────────────────────────────

    def construct_search_text(self, payload: dict, extra: list[str] = None) -> str:
        return _join(payload, ["functional_record_id", *self.search_keys], extra)

    def construct_record_name(self, payload: dict, extra: list[str] = None) -> str:
        return _join(payload, self.name_keys, extra)

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
