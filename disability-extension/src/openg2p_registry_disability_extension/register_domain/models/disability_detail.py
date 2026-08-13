"""DO.DR.04 DisabilityDetails — one row per impairment.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.

The standard gives this object 0...* cardinality on the person, which is the
whole reason it is a table and not four columns: co-occurring impairments are
the norm, not the exception, and collapsing them to a single "primary" loses the
combination that actually determines support needs.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceDisabilityDetail
from .enums import (
    AgeOnsetBandEnum,
    AssessmentMethodEnum,
    ImpairmentCauseEnum,
    ImpairmentLevelEnum,
    ImpairmentTypeEnum,
)


class G2PDisabilityDetail:
    impairment_type: Mapped[ImpairmentTypeEnum] = mapped_column(String, nullable=True, index=True)
    impairment_level: Mapped[ImpairmentLevelEnum] = mapped_column(String, nullable=True, index=True)
    impairment_cause: Mapped[ImpairmentCauseEnum] = mapped_column(String, nullable=True)

    # DO.DR.04 `age_on_set`, kept under the standard's spelling. The band is the
    # reporting dimension and is answerable when the number is not.
    age_on_set: Mapped[int] = mapped_column(Integer, nullable=True)
    age_onset_band: Mapped[AgeOnsetBandEnum] = mapped_column(String, nullable=True)
    onset_date: Mapped[Date] = mapped_column(Date, nullable=True)

    is_primary_impairment: Mapped[bool] = mapped_column(Boolean, nullable=True)
    # ICD-11 / ICF code where a clinical assessment produced one.
    diagnosis_code: Mapped[str] = mapped_column(String, nullable=True)
    diagnosis_description: Mapped[str] = mapped_column(String, nullable=True)

    assessment_method: Mapped[AssessmentMethodEnum] = mapped_column(String, nullable=True)
    assessed_on: Mapped[Date] = mapped_column(Date, nullable=True)
    assessed_by: Mapped[str] = mapped_column(String, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterDisabilityDetail(G2PRegister, G2PDisabilityDetail):
    __tablename__ = "g2p_register_disability_details"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceDisabilityDetail().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceDisabilityDetail().construct_record_name(self.to_dict())


class G2PRegisterHistoryDisabilityDetail(G2PRegisterHistory, G2PDisabilityDetail):
    __tablename__ = "g2p_register_history_disability_details"


class G2PIntakeFormDisabilityDetail(G2PIntakeForm, G2PRegister, G2PDisabilityDetail):
    __tablename__ = "g2p_intake_form_disability_details"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceDisabilityDetail().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceDisabilityDetail().construct_intake_record_name(
            self.to_dict()
        )
