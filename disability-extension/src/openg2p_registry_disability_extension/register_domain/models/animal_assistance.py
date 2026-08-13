"""DO.DR.10 AnimalAssistance — assistance animals required or received.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.
One of the five DO.DR.05 DisabilitySupport sub-registers.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceAnimalAssistance
from .enums import AnimalAssistanceTypeEnum, ProvisionSourceEnum, SupportStatusEnum


class G2PAnimalAssistance:
    # DO.DR.10 `type`.
    animal_assistance_type: Mapped[AnimalAssistanceTypeEnum] = mapped_column(
        String, nullable=True, index=True
    )
    support_status: Mapped[SupportStatusEnum] = mapped_column(String, nullable=True, index=True)

    animal_name: Mapped[str] = mapped_column(String, nullable=True)
    # An assistance animal's certification is what grants right-of-access to
    # transport and public buildings, so it travels with the record.
    certification_reference: Mapped[str] = mapped_column(String, nullable=True)
    certification_expiry_date: Mapped[Date] = mapped_column(Date, nullable=True)
    provision_source: Mapped[ProvisionSourceEnum] = mapped_column(String, nullable=True)
    provider_name: Mapped[str] = mapped_column(String, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterAnimalAssistance(G2PRegister, G2PAnimalAssistance):
    __tablename__ = "g2p_register_animal_assistances"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAnimalAssistance().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAnimalAssistance().construct_record_name(self.to_dict())


class G2PRegisterHistoryAnimalAssistance(G2PRegisterHistory, G2PAnimalAssistance):
    __tablename__ = "g2p_register_history_animal_assistances"


class G2PIntakeFormAnimalAssistance(G2PIntakeForm, G2PRegister, G2PAnimalAssistance):
    __tablename__ = "g2p_intake_form_animal_assistances"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceAnimalAssistance().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceAnimalAssistance().construct_intake_record_name(
            self.to_dict()
        )
