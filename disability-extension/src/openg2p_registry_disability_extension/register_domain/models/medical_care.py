"""DO.DR.08 MedicalCare — chronic care with recurring out-of-pocket cost.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.
One of the five DO.DR.05 DisabilitySupport sub-registers.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceMedicalCare
from .enums import MedicalCareTypeEnum, SupportFrequencyEnum, SupportStatusEnum


class G2PMedicalCare:
    # DO.DR.08 `type`.
    medical_care_type: Mapped[MedicalCareTypeEnum] = mapped_column(
        String, nullable=True, index=True
    )
    support_status: Mapped[SupportStatusEnum] = mapped_column(String, nullable=True, index=True)
    frequency: Mapped[SupportFrequencyEnum] = mapped_column(String, nullable=True)

    # The standard singles this care out precisely because it "can generate
    # significant out-of-pocket costs" — so the cost is a column, and Numeric
    # rather than Float because money compared with a float is money reported
    # wrongly. Currency comes from the deployment's country pack, not per row.
    monthly_out_of_pocket_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=True)
    is_covered_by_insurance: Mapped[bool] = mapped_column(Boolean, nullable=True)

    provider_name: Mapped[str] = mapped_column(String, nullable=True)
    facility_identifier: Mapped[str] = mapped_column(String, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterMedicalCare(G2PRegister, G2PMedicalCare):
    __tablename__ = "g2p_register_medical_cares"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceMedicalCare().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceMedicalCare().construct_record_name(self.to_dict())


class G2PRegisterHistoryMedicalCare(G2PRegisterHistory, G2PMedicalCare):
    __tablename__ = "g2p_register_history_medical_cares"


class G2PIntakeFormMedicalCare(G2PIntakeForm, G2PRegister, G2PMedicalCare):
    __tablename__ = "g2p_intake_form_medical_cares"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceMedicalCare().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceMedicalCare().construct_intake_record_name(self.to_dict())
