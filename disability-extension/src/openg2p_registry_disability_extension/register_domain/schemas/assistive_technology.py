from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import AssistiveTechnologyTypeEnum, ProvisionSourceEnum, SupportStatusEnum


class G2PSchemaAssistiveTechnology:
    assistive_technology_type: Optional[AssistiveTechnologyTypeEnum] = None
    support_status: Optional[SupportStatusEnum] = None

    provision_source: Optional[ProvisionSourceEnum] = None
    provider_name: Optional[str] = None
    provided_on: Optional[date] = None
    expected_replacement_date: Optional[date] = None
    product_identifier: Optional[str] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaAssistiveTechnology(G2PRegisterBaseSchema, G2PSchemaAssistiveTechnology):
    """
    Schema for AssistiveTechnology register (SPDCI DO.DR.07).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaAssistiveTechnology(G2PRegisterHistorySchema):
    """Schema for AssistiveTechnology history."""


class G2PIntakeFormSchemaAssistiveTechnology(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaAssistiveTechnology
):
    """Schema for AssistiveTechnology intake form."""
