"""DO.DR.09 HousingSupport — support addressing barriers in housing.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.
One of the five DO.DR.05 DisabilitySupport sub-registers.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceHousingSupport
from .enums import HousingSupportTypeEnum, ProvisionSourceEnum, SupportStatusEnum


class G2PHousingSupport:
    # DO.DR.09 `type`.
    housing_support_type: Mapped[HousingSupportTypeEnum] = mapped_column(
        String, nullable=True, index=True
    )
    support_status: Mapped[SupportStatusEnum] = mapped_column(String, nullable=True, index=True)

    provision_source: Mapped[ProvisionSourceEnum] = mapped_column(String, nullable=True)
    provider_name: Mapped[str] = mapped_column(String, nullable=True)
    completed_on: Mapped[Date] = mapped_column(Date, nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterHousingSupport(G2PRegister, G2PHousingSupport):
    __tablename__ = "g2p_register_housing_supports"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceHousingSupport().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceHousingSupport().construct_record_name(self.to_dict())


class G2PRegisterHistoryHousingSupport(G2PRegisterHistory, G2PHousingSupport):
    __tablename__ = "g2p_register_history_housing_supports"


class G2PIntakeFormHousingSupport(G2PIntakeForm, G2PRegister, G2PHousingSupport):
    __tablename__ = "g2p_intake_form_housing_supports"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceHousingSupport().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceHousingSupport().construct_intake_record_name(self.to_dict())
