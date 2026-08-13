from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import AnimalAssistanceTypeEnum, ProvisionSourceEnum, SupportStatusEnum


class G2PSchemaAnimalAssistance:
    animal_assistance_type: Optional[AnimalAssistanceTypeEnum] = None
    support_status: Optional[SupportStatusEnum] = None

    animal_name: Optional[str] = None
    certification_reference: Optional[str] = None
    certification_expiry_date: Optional[date] = None
    provision_source: Optional[ProvisionSourceEnum] = None
    provider_name: Optional[str] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaAnimalAssistance(G2PRegisterBaseSchema, G2PSchemaAnimalAssistance):
    """
    Schema for AnimalAssistance register (SPDCI DO.DR.10).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaAnimalAssistance(G2PRegisterHistorySchema):
    """Schema for AnimalAssistance history."""


class G2PIntakeFormSchemaAnimalAssistance(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaAnimalAssistance
):
    """Schema for AnimalAssistance intake form."""
