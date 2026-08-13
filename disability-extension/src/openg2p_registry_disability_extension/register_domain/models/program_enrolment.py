"""DO.DR.03 `programs_enrolments` — other programmes the person benefits from.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.

The standard's stated purpose for this field is interoperability with SP systems:
a benefit administrator needs to know what the person already receives before it
decides what to award.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceProgramEnrolment
from .enums import ProgramEnrolmentStatusEnum


class G2PProgramEnrolment:
    # Free string rather than the ProgramEnum type, because the authoritative
    # list is `PROGRAM_NAME` in g2p_attribute_values and a country pack replaces
    # it wholesale. Constraining the column to the shipped defaults would make
    # every country's own programme names unstorable.
    program_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    program_identifier: Mapped[str] = mapped_column(String, nullable=True)
    implementing_agency: Mapped[str] = mapped_column(String, nullable=True)

    enrolment_status: Mapped[ProgramEnrolmentStatusEnum] = mapped_column(
        String, nullable=True, index=True
    )
    beneficiary_identifier: Mapped[str] = mapped_column(String, nullable=True)
    enrolment_start_date: Mapped[Date] = mapped_column(Date, nullable=True)
    enrolment_end_date: Mapped[Date] = mapped_column(Date, nullable=True)

    benefit_type: Mapped[str] = mapped_column(String, nullable=True)
    benefit_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=True)
    benefit_frequency: Mapped[str] = mapped_column(String, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterProgramEnrolment(G2PRegister, G2PProgramEnrolment):
    __tablename__ = "g2p_register_program_enrolments"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceProgramEnrolment().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceProgramEnrolment().construct_record_name(self.to_dict())


class G2PRegisterHistoryProgramEnrolment(G2PRegisterHistory, G2PProgramEnrolment):
    __tablename__ = "g2p_register_history_program_enrolments"


class G2PIntakeFormProgramEnrolment(G2PIntakeForm, G2PRegister, G2PProgramEnrolment):
    __tablename__ = "g2p_intake_form_program_enrolments"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceProgramEnrolment().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceProgramEnrolment().construct_intake_record_name(
            self.to_dict()
        )
