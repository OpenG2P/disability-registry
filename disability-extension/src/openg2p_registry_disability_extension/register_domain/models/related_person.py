"""DO.DR.02 Member `related_person` — people related to the registrant.

`link_internal_record_id` -> PersonWithDisability.internal_record_id.

This registry has no group register, so relationships are recorded here rather
than inferred from shared household membership. That is a deliberate fit to the
domain: the people who matter to a disability case — a guardian, a primary
caregiver, an emergency contact — are frequently NOT co-resident, and a
household roster would miss exactly them.

`related_person_record_id` optionally points at another PersonWithDisability row
when the relative is themselves registered here.
"""

from openg2p_registry_core.models import G2PRegister, G2PRegisterHistory
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServiceRelatedPerson
from .enums import RelationshipTypeEnum


class G2PRelatedPerson:
    relationship_type: Mapped[RelationshipTypeEnum] = mapped_column(
        String, nullable=True, index=True
    )
    related_person_name: Mapped[str] = mapped_column(String, nullable=True)
    related_person_identifier: Mapped[str] = mapped_column(String, nullable=True, index=True)
    # Set when the relative is also registered here; left null for an external
    # person. Not a foreign key — the relative may be registered later, and a
    # constraint would make the order of data entry load-bearing.
    related_person_record_id: Mapped[str] = mapped_column(String, nullable=True, index=True)

    related_person_phone: Mapped[str] = mapped_column(String, nullable=True)
    related_person_birth_date: Mapped[Date] = mapped_column(Date, nullable=True)

    is_primary_caregiver: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_legal_guardian: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_co_resident: Mapped[bool] = mapped_column(Boolean, nullable=True)

    registration_date: Mapped[Date] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Date] = mapped_column(Date, nullable=True)


class G2PRegisterRelatedPerson(G2PRegister, G2PRelatedPerson):
    __tablename__ = "g2p_register_related_persons"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceRelatedPerson().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceRelatedPerson().construct_record_name(self.to_dict())


class G2PRegisterHistoryRelatedPerson(G2PRegisterHistory, G2PRelatedPerson):
    __tablename__ = "g2p_register_history_related_persons"


class G2PIntakeFormRelatedPerson(G2PIntakeForm, G2PRegister, G2PRelatedPerson):
    __tablename__ = "g2p_intake_form_related_persons"

    def get_search_text_fields(self) -> str:
        return G2PRegisterDomainServiceRelatedPerson().construct_search_text(self.to_dict())

    def get_record_name_fields(self) -> str:
        return G2PRegisterDomainServiceRelatedPerson().construct_intake_record_name(self.to_dict())
