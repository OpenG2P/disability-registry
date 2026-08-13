from datetime import date
from decimal import Decimal
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import HousingSupportTypeEnum, ProvisionSourceEnum, SupportStatusEnum


class G2PSchemaHousingSupport:
    housing_support_type: Optional[HousingSupportTypeEnum] = None
    support_status: Optional[SupportStatusEnum] = None

    provision_source: Optional[ProvisionSourceEnum] = None
    provider_name: Optional[str] = None
    completed_on: Optional[date] = None
    estimated_cost: Optional[Decimal] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaHousingSupport(G2PRegisterBaseSchema, G2PSchemaHousingSupport):
    """
    Schema for HousingSupport register (SPDCI DO.DR.09).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaHousingSupport(G2PRegisterHistorySchema):
    """Schema for HousingSupport history."""


class G2PIntakeFormSchemaHousingSupport(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaHousingSupport
):
    """Schema for HousingSupport intake form."""
