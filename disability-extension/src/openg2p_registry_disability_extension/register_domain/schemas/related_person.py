from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import RelationshipTypeEnum


class G2PSchemaRelatedPerson:
    relationship_type: Optional[RelationshipTypeEnum] = None
    related_person_name: Optional[str] = None
    related_person_identifier: Optional[str] = None
    related_person_record_id: Optional[str] = None

    related_person_phone: Optional[str] = None
    related_person_birth_date: Optional[date] = None

    is_primary_caregiver: Optional[bool] = None
    is_legal_guardian: Optional[bool] = None
    is_emergency_contact: Optional[bool] = None
    is_co_resident: Optional[bool] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaRelatedPerson(G2PRegisterBaseSchema, G2PSchemaRelatedPerson):
    """
    Schema for RelatedPerson register (SPDCI DO.DR.02 related_person).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaRelatedPerson(G2PRegisterHistorySchema):
    """Schema for RelatedPerson history."""


class G2PIntakeFormSchemaRelatedPerson(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaRelatedPerson
):
    """Schema for RelatedPerson intake form."""
