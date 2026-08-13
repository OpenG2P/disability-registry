"""Recompute the person-level unmet-support-need summary.

`PersonWithDisability.unmet_support_needs_count` / `has_unmet_support_need` are
denormalised from the five DO.DR.05 support sub-registers. They are what the
dashboards, the maps and any targeting query group by, so they must be rebuilt
whenever a support row changes — not only when the person row does.

"Unmet" is defined as a support row whose `support_status` is REQUIRED or
PARTIALLY_RECEIVED. NOT_REQUIRED and DISCONTINUED are explicit statements that
nothing is owed; RECEIVING/RECEIVED are met. A row with no status at all is not
counted — an unanswered question is not evidence of unmet need, and counting it
would inflate every unmet-need figure the registry publishes.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_logger = logging.getLogger("g2p-register-domain-service")

# Statuses that represent a need the person still has.
UNMET_STATUSES = {"REQUIRED", "PARTIALLY_RECEIVED"}


def _support_models():
    """Imported lazily: these modules import the services package, so importing
    them at module load time would close an import cycle."""
    from ...models.animal_assistance import G2PRegisterAnimalAssistance
    from ...models.assistive_technology import G2PRegisterAssistiveTechnology
    from ...models.housing_support import G2PRegisterHousingSupport
    from ...models.human_assistance import G2PRegisterHumanAssistance
    from ...models.medical_care import G2PRegisterMedicalCare

    return (
        G2PRegisterHumanAssistance,
        G2PRegisterAssistiveTechnology,
        G2PRegisterMedicalCare,
        G2PRegisterHousingSupport,
        G2PRegisterAnimalAssistance,
    )


def is_unmet(support_status) -> bool:
    if support_status is None:
        return False
    value = getattr(support_status, "value", support_status)
    return str(value).strip().upper() in UNMET_STATUSES


async def recompute_support_summary(session: AsyncSession, person_internal_record_id: str) -> None:
    """Refresh the summary columns on one person from their support rows."""
    if not person_internal_record_id:
        return

    from ...models.person_with_disability import G2PRegisterPersonWithDisability

    person = await session.get(G2PRegisterPersonWithDisability, person_internal_record_id)
    if not person:
        return

    unmet = 0
    for model in _support_models():
        result = await session.execute(
            select(model.support_status).where(
                model.link_internal_record_id == person_internal_record_id,
                # ACTIVE only: a retired support row is history, not a live need.
                model.record_status == "ACTIVE",
            )
        )
        unmet += sum(1 for (status,) in result.all() if is_unmet(status))

    person.unmet_support_needs_count = unmet
    person.has_unmet_support_need = unmet > 0

    _logger.info(
        "Recomputed support summary for person %s: %s unmet support need(s)",
        person_internal_record_id,
        unmet,
    )
