from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import (
    CaregiverRelationshipEnum,
    HumanAssistanceTypeEnum,
    SupportFrequencyEnum,
    SupportStatusEnum,
)


class G2PSchemaHumanAssistance:
    assistance_type: Optional[HumanAssistanceTypeEnum] = None
    frequency: Optional[SupportFrequencyEnum] = None
    support_status: Optional[SupportStatusEnum] = None

    caregiver_name: Optional[str] = None
    caregiver_identifier: Optional[str] = None
    caregiver_phone: Optional[str] = None
    caregiver_relationship: Optional[CaregiverRelationshipEnum] = None
    is_paid_caregiver: Optional[bool] = None
    hours_per_week: Optional[int] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaHumanAssistance(G2PRegisterBaseSchema, G2PSchemaHumanAssistance):
    """
    Schema for HumanAssistance register (SPDCI DO.DR.06).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaHumanAssistance(G2PRegisterHistorySchema):
    """Schema for HumanAssistance history."""


class G2PIntakeFormSchemaHumanAssistance(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaHumanAssistance
):
    """Schema for HumanAssistance intake form."""
