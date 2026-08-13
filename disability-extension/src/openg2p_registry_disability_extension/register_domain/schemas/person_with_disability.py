from datetime import date
from typing import List, Optional

from openg2p_registry_core.schemas import (
    G2PGeoHistorySchema,
    G2PGeoSchema,
    G2PIntakeFormSchemaBase,
    G2PPersonHistorySchema,
    G2PPersonSchema,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import (
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


class G2PSchemaPersonWithDisability:
    foundational_id_masked: Optional[str] = None
    foundational_id_verification_status: Optional[VerificationStatusEnum] = None
    identity_evidence_type: Optional[IdentityEvidenceTypeEnum] = None
    registration_channel: Optional[RegistrationChannelEnum] = None
    legacy_program_ids: Optional[dict] = None

    full_name: Optional[str] = None
    alias_names: Optional[List[str]] = None
    death_date: Optional[date] = None
    estimated_age: Optional[int] = None

    self_id_disability: Optional[bool] = None
    employment_status: Optional[EmploymentStatusEnum] = None

    disability_status: Optional[DisabilityStatusEnum] = None
    disability_status_level: Optional[DisabilityStatusLevelEnum] = None
    support_needs_level: Optional[SupportNeedsLevelEnum] = None

    assessment_date: Optional[date] = None
    assessment_authority: Optional[str] = None
    disability_certificate_number: Optional[str] = None
    certificate_issue_date: Optional[date] = None
    certificate_expiry_date: Optional[date] = None
    next_reassessment_date: Optional[date] = None

    transport_requirement: Optional[TransportRequirementEnum] = None
    housing_type: Optional[HousingTypeEnum] = None
    lives_alone: Optional[bool] = None

    communication_needs: Optional[List[CommunicationNeedEnum]] = None
    preferred_contact_method: Optional[PreferredContactMethodEnum] = None
    contact_person_name: Optional[str] = None
    contact_person_phone: Optional[str] = None
    legal_capacity_status: Optional[LegalCapacityStatusEnum] = None
    guardian_required: Optional[bool] = None

    unmet_support_needs_count: Optional[int] = None
    has_unmet_support_need: Optional[bool] = None


class G2PRegisterSchemaPersonWithDisability(
    G2PRegisterBaseSchema, G2PPersonSchema, G2PGeoSchema, G2PSchemaPersonWithDisability
):
    """
    Schema for PersonWithDisability register.
    Inherits fields from G2PRegisterBaseSchema, G2PPersonSchema, and G2PGeoSchema.
    Attributes inherited from G2PSchemaPersonWithDisability are specific to the
    Disability Registry domain (SPDCI DO.DR.01 / DO.DR.02 / DO.DR.03).
    """


class G2PRegisterHistorySchemaPersonWithDisability(
    G2PRegisterHistorySchema, G2PPersonHistorySchema, G2PGeoHistorySchema
):
    """
    Schema for PersonWithDisability history.
    Inherits core history payloads only.
    """


class G2PIntakeFormSchemaPersonWithDisability(
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PPersonSchema,
    G2PGeoSchema,
    G2PSchemaPersonWithDisability,
):
    """
    Schema for PersonWithDisability intake form.
    """
