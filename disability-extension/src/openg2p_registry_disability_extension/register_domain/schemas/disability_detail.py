from datetime import date
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import (
    AgeOnsetBandEnum,
    AssessmentMethodEnum,
    ImpairmentCauseEnum,
    ImpairmentLevelEnum,
    ImpairmentTypeEnum,
)


class G2PSchemaDisabilityDetail:
    impairment_type: Optional[ImpairmentTypeEnum] = None
    impairment_level: Optional[ImpairmentLevelEnum] = None
    impairment_cause: Optional[ImpairmentCauseEnum] = None

    age_on_set: Optional[int] = None
    age_onset_band: Optional[AgeOnsetBandEnum] = None
    onset_date: Optional[date] = None

    is_primary_impairment: Optional[bool] = None
    diagnosis_code: Optional[str] = None
    diagnosis_description: Optional[str] = None

    assessment_method: Optional[AssessmentMethodEnum] = None
    assessed_on: Optional[date] = None
    assessed_by: Optional[str] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaDisabilityDetail(G2PRegisterBaseSchema, G2PSchemaDisabilityDetail):
    """
    Schema for DisabilityDetail register (SPDCI DO.DR.04).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaDisabilityDetail(G2PRegisterHistorySchema):
    """Schema for DisabilityDetail history."""


class G2PIntakeFormSchemaDisabilityDetail(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaDisabilityDetail
):
    """Schema for DisabilityDetail intake form."""
