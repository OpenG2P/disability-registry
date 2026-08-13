from datetime import date
from decimal import Decimal
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import MedicalCareTypeEnum, SupportFrequencyEnum, SupportStatusEnum


class G2PSchemaMedicalCare:
    medical_care_type: Optional[MedicalCareTypeEnum] = None
    support_status: Optional[SupportStatusEnum] = None
    frequency: Optional[SupportFrequencyEnum] = None

    monthly_out_of_pocket_cost: Optional[Decimal] = None
    is_covered_by_insurance: Optional[bool] = None

    provider_name: Optional[str] = None
    facility_identifier: Optional[str] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaMedicalCare(G2PRegisterBaseSchema, G2PSchemaMedicalCare):
    """
    Schema for MedicalCare register (SPDCI DO.DR.08).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaMedicalCare(G2PRegisterHistorySchema):
    """Schema for MedicalCare history."""


class G2PIntakeFormSchemaMedicalCare(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaMedicalCare
):
    """Schema for MedicalCare intake form."""
