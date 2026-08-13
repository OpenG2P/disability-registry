"""DO.DR.06 HumanAssistance — care and personal assistance.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.

One of the five DO.DR.05 DisabilitySupport sub-registers. `support_status`
carries the required/receiving distinction that makes the unmet-need report
possible.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceHumanAssistance
from .enums import (
    CaregiverRelationshipEnum,
    HumanAssistanceTypeEnum,
    SupportFrequencyEnum,
    SupportStatusEnum,
)


class G2PHumanAssistance:
    # DO.DR.06 `type`. Named explicitly rather than `type` so the column does not
    # shadow the builtin in the Pydantic schema; the DCI template maps it back.
    assistance_type: Mapped[HumanAssistanceTypeEnum] = mapped_column(
        String, nullable=True, index=True
    )
    frequency: Mapped[SupportFrequencyEnum] = mapped_column(String, nullable=True)
    support_status: Mapped[SupportStatusEnum] = mapped_column(String, nullable=True, index=True)

    # DO.DR.06 `caregiver` + `relationship`.
    caregiver_name: Mapped[str] = mapped_column(String, nullable=True)
    caregiver_identifier: Mapped[str] = mapped_column(String, nullable=True)
    caregiver_phone: Mapped[str] = mapped_column(String, nullable=True)
    caregiver_relationship: Mapped[CaregiverRelationshipEnum] = mapped_column(
        String, nullable=True
    )
    # Unpaid family care is the invisible majority of disability support; a
    # caregiver allowance cannot be targeted without recording it.
    is_paid_caregiver: Mapped[bool] = mapped_column(Boolean, nullable=True)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterHumanAssistance(G2PRegister, G2PHumanAssistance):
    __tablename__ = "g2p_register_human_assistances"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceHumanAssistance().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceHumanAssistance().construct_record_name(self.to_dict())


class G2PRegisterHistoryHumanAssistance(G2PRegisterHistory, G2PHumanAssistance):
    __tablename__ = "g2p_register_history_human_assistances"


class G2PIntakeFormHumanAssistance(G2PIntakeForm, G2PRegister, G2PHumanAssistance):
    __tablename__ = "g2p_intake_form_human_assistances"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceHumanAssistance().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceHumanAssistance().construct_intake_record_name(
            self.to_dict()
        )
