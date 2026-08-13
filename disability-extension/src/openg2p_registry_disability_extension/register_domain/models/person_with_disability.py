"""DO.DR.03 PersonwithDisability — the registry's single master register.

Composed of three SPDCI objects rather than one, because they describe the same
row from different angles:
  * DO.DR.01 DRPerson — identity, name, sex, birth/death, contacts  -> G2PPerson
  * DO.DR.02 Member   — socio-economic attributes, self-identification
  * DO.DR.03 PWD      — assessed status, level, transport, housing

This registry has NO group register. A `Member` in the standard belongs to a
household; here the person IS the record, and the household relationships that
matter for disability support are carried as `RelatedPerson` rows rather than by
linking to a group register.
"""

from openg2p_registry_core.models import (
    G2PGeo,
    G2PGeoHistory,
    G2PPerson,
    G2PPersonHistory,
    G2PRegister,
    G2PRegisterHistory,
)
from openg2p_registry_core.models.g2p_intake_form import G2PIntakeForm
from sqlalchemy import JSON, Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..services import G2PRegisterDomainServicePersonWithDisability
from .enums import (
    CommunicationNeedEnum,
    DisabilityStatusEnum,
    DisabilityStatusLevelEnum,
    EmploymentStatusEnum,
    HousingTypeEnum,
    IdentityEvidenceTypeEnum,
    LegalCapacityStatusEnum,
    PreferredContactMethodEnum,
    RegistrationChannelEnum,
    SupportNeedsLevelEnum,
    TransportRequirementEnum,
    VerificationStatusEnum,
)


class G2PPersonWithDisability:
    # ── Identity and provenance ──────────────────────────────────────────────
    # `foundational_id`, names, gender, birth_date, contacts, marital_status,
    # occupation, income_level, language_code, education_level and
    # registration_date all come from G2PPerson — see DO.DR.01/DO.DR.02.
    foundational_id_masked: Mapped[str] = mapped_column(String, nullable=True)
    foundational_id_verification_status: Mapped[VerificationStatusEnum] = mapped_column(
        String, nullable=True
    )
    identity_evidence_type: Mapped[IdentityEvidenceTypeEnum] = mapped_column(String, nullable=True)
    registration_channel: Mapped[RegistrationChannelEnum] = mapped_column(String, nullable=True)
    legacy_program_ids: Mapped[dict] = mapped_column(JSON, nullable=True)

    # DO.DR.01 `name` in displayable form, and `death_date`.
    full_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    alias_names: Mapped[list] = mapped_column(JSON, nullable=True)
    death_date: Mapped[Date] = mapped_column(Date, nullable=True)
    estimated_age: Mapped[int] = mapped_column(Integer, nullable=True)

    # ── DO.DR.02 self-identification and socio-economic attributes ───────────
    # `self_id_disability` is the person's own answer; `disability_status` below
    # is the assessment's. The standard carries both and so do we.
    self_id_disability: Mapped[bool] = mapped_column(Boolean, nullable=True)
    employment_status: Mapped[EmploymentStatusEnum] = mapped_column(String, nullable=True)

    # ── DO.DR.03 assessed status ─────────────────────────────────────────────
    disability_status: Mapped[DisabilityStatusEnum] = mapped_column(
        String, nullable=True, index=True
    )
    disability_status_level: Mapped[DisabilityStatusLevelEnum] = mapped_column(
        String, nullable=True, index=True
    )
    support_needs_level: Mapped[SupportNeedsLevelEnum] = mapped_column(String, nullable=True)

    assessment_date: Mapped[Date] = mapped_column(Date, nullable=True)
    assessment_authority: Mapped[str] = mapped_column(String, nullable=True)
    disability_certificate_number: Mapped[str] = mapped_column(String, nullable=True, index=True)
    certificate_issue_date: Mapped[Date] = mapped_column(Date, nullable=True)
    # Re-assessment is the single most common reason a disability record goes
    # stale, so the expiry is a first-class column rather than a note.
    certificate_expiry_date: Mapped[Date] = mapped_column(Date, nullable=True)
    next_reassessment_date: Mapped[Date] = mapped_column(Date, nullable=True)

    # ── DO.DR.03 living situation and mobility ───────────────────────────────
    transport_requirement: Mapped[TransportRequirementEnum] = mapped_column(String, nullable=True)
    housing_type: Mapped[HousingTypeEnum] = mapped_column(String, nullable=True)
    lives_alone: Mapped[bool] = mapped_column(Boolean, nullable=True)

    # ── Accessibility, capacity and contact ──────────────────────────────────
    # A list because these co-occur (see CommunicationNeedEnum).
    communication_needs: Mapped[list] = mapped_column(JSON, nullable=True)
    preferred_contact_method: Mapped[PreferredContactMethodEnum] = mapped_column(
        String, nullable=True
    )
    contact_person_name: Mapped[str] = mapped_column(String, nullable=True)
    contact_person_phone: Mapped[str] = mapped_column(String, nullable=True)
    legal_capacity_status: Mapped[LegalCapacityStatusEnum] = mapped_column(String, nullable=True)
    guardian_required: Mapped[bool] = mapped_column(Boolean, nullable=True)

    # ── Derived summary of the support sub-registers ─────────────────────────
    # Denormalised on purpose: "how many people have an unmet support need" is
    # the registry's headline question, and answering it by fanning out over five
    # child tables per row makes every dashboard and every targeting query slow.
    # Recomputed by the domain service, never edited by hand.
    unmet_support_needs_count: Mapped[int] = mapped_column(Integer, nullable=True)
    has_unmet_support_need: Mapped[bool] = mapped_column(Boolean, nullable=True, index=True)


class G2PRegisterPersonWithDisability(G2PRegister, G2PPerson, G2PGeo, G2PPersonWithDisability):
    __tablename__ = "g2p_register_persons_with_disability"

    def get_record_name_fields(self) -> str:
        """Return person fields used to build record_name."""
        return G2PRegisterDomainServicePersonWithDisability().construct_record_name(self.to_dict())

    def get_search_text_fields(self) -> str:
        """Return person fields used to build search_text."""
        return G2PRegisterDomainServicePersonWithDisability().construct_search_text(self.to_dict())


class G2PRegisterHistoryPersonWithDisability(
    G2PRegisterHistory, G2PPersonHistory, G2PGeoHistory, G2PPersonWithDisability
):
    __tablename__ = "g2p_register_history_persons_with_disability"


class G2PIntakeFormPersonWithDisability(
    G2PIntakeForm, G2PRegister, G2PPerson, G2PGeo, G2PPersonWithDisability
):
    __tablename__ = "g2p_intake_form_persons_with_disability"

    def get_record_name_fields(self) -> str:
        """Return person fields used to build record_name."""
        return G2PRegisterDomainServicePersonWithDisability().construct_intake_record_name(
            self.to_dict()
        )

    def get_search_text_fields(self) -> str:
        """Return person fields used to build search_text."""
        return G2PRegisterDomainServicePersonWithDisability().construct_search_text(self.to_dict())
