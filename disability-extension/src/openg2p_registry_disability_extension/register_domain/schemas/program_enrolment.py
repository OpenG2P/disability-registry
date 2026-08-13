from datetime import date
from decimal import Decimal
from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)

from ..models.enums import ProgramEnrolmentStatusEnum


class G2PSchemaProgramEnrolment:
    program_name: Optional[str] = None
    program_identifier: Optional[str] = None
    implementing_agency: Optional[str] = None

    enrolment_status: Optional[ProgramEnrolmentStatusEnum] = None
    beneficiary_identifier: Optional[str] = None
    enrolment_start_date: Optional[date] = None
    enrolment_end_date: Optional[date] = None

    benefit_type: Optional[str] = None
    benefit_amount: Optional[Decimal] = None
    benefit_frequency: Optional[str] = None

    registration_date: Optional[date] = None
    last_updated: Optional[date] = None


class G2PRegisterSchemaProgramEnrolment(G2PRegisterBaseSchema, G2PSchemaProgramEnrolment):
    """
    Schema for ProgramEnrolment register (SPDCI DO.DR.03 programs_enrolments).
    link_internal_record_id -> PersonWithDisability.internal_record_id
    """


class G2PRegisterHistorySchemaProgramEnrolment(G2PRegisterHistorySchema):
    """Schema for ProgramEnrolment history."""


class G2PIntakeFormSchemaProgramEnrolment(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaProgramEnrolment
):
    """Schema for ProgramEnrolment intake form."""
