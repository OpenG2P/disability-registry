"""Read-only view of the computed SUPPORT_NEED score.

Scores live in registry-core's `g2p_register_scores` (register_id -> the `Score`
CORE_TABLE definition), not in an extension table — this schema exists so the
staff API can present them alongside the person's own fields.
"""

from typing import Optional

from openg2p_registry_core.schemas import (
    G2PIntakeFormSchemaBase,
    G2PRegisterBaseSchema,
    G2PRegisterHistorySchema,
)


class G2PSchemaSupportNeedScore:
    support_need_score: Optional[str] = None
    support_need_score_type: Optional[str] = None


class G2PSupportNeedScoreSchema(G2PRegisterBaseSchema, G2PSchemaSupportNeedScore):
    """Schema for the SUPPORT_NEED score attached to a PersonWithDisability."""


class G2PRegisterHistorySchemaSupportNeedScore(G2PRegisterHistorySchema):
    """Schema for support-need score history."""


class G2PIntakeFormSchemaSupportNeedScore(
    G2PIntakeFormSchemaBase, G2PRegisterBaseSchema, G2PSchemaSupportNeedScore
):
    """Schema for the support-need score on an intake form."""
