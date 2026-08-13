"""DO.DR.07 AssistiveTechnology — assistive products required or received.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.
One of the five DO.DR.05 DisabilitySupport sub-registers.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceAssistiveTechnology
from .enums import AssistiveTechnologyTypeEnum, ProvisionSourceEnum, SupportStatusEnum


class G2PAssistiveTechnology:
    # DO.DR.07 `type` (WHO Priority Assistive Products List).
    assistive_technology_type: Mapped[AssistiveTechnologyTypeEnum] = mapped_column(
        String, nullable=True, index=True
    )
    support_status: Mapped[SupportStatusEnum] = mapped_column(String, nullable=True, index=True)

    provision_source: Mapped[ProvisionSourceEnum] = mapped_column(String, nullable=True)
    provider_name: Mapped[str] = mapped_column(String, nullable=True)
    provided_on: Mapped[Date] = mapped_column(Date, nullable=True)
    # Assistive products wear out and children outgrow them; a device provided
    # once is not a need met forever, and the replacement date is what turns a
    # RECEIVED row back into a REQUIRED one.
    expected_replacement_date: Mapped[Date] = mapped_column(Date, nullable=True)
    product_identifier: Mapped[str] = mapped_column(String, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterAssistiveTechnology(G2PRegister, G2PAssistiveTechnology):
    __tablename__ = "g2p_register_assistive_technologies"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAssistiveTechnology().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAssistiveTechnology().construct_record_name(self.to_dict())


class G2PRegisterHistoryAssistiveTechnology(G2PRegisterHistory, G2PAssistiveTechnology):
    __tablename__ = "g2p_register_history_assistive_technologies"


class G2PIntakeFormAssistiveTechnology(G2PIntakeForm, G2PRegister, G2PAssistiveTechnology):
    __tablename__ = "g2p_intake_form_assistive_technologies"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAssistiveTechnology().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAssistiveTechnology().construct_intake_record_name(
            self.to_dict()
        )
