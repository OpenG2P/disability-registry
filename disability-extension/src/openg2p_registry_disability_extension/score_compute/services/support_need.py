"""SUPPORT_NEED score for a person with disability.

Weighted sum over the attributes named in
`g2p_register_score_contributing_attributes`, with a categorical-to-numeric step
that a plain sum cannot do on its own: most of what determines support need in
this registry is an enum (severity level, support-needs level), not a number.

The score is a TRIAGE aid — it orders a caseload so the most support-dependent
people are reached first. It is deliberately not an eligibility rule: entitlement
in a rights-based disability system follows from assessment and law, not from a
weighted average, and a score used as a gate would quietly become one.
"""

import logging
from typing import Any

from openg2p_registry_core.interfaces.g2p_score_compute_interface import (
    G2PScoreComputeInterface,
)

_logger = logging.getLogger(__name__)

# Ordinal maps for the categorical contributors. Normalised to 0.0 - 1.0 so a
# weight in the metadata means the same thing regardless of which scale it is
# applied to.
_ORDINAL_SCALES: dict[str, dict[str, float]] = {
    "disability_status_level": {
        "NONE": 0.0,
        "MILD": 0.25,
        "MODERATE": 0.5,
        "SEVERE": 0.75,
        "PROFOUND": 1.0,
    },
    "support_needs_level": {
        "INDEPENDENT": 0.0,
        "INTERMITTENT_SUPPORT": 0.25,
        "LIMITED_SUPPORT": 0.5,
        "EXTENSIVE_SUPPORT": 0.75,
        "PERVASIVE_SUPPORT": 1.0,
    },
    "impairment_level": {
        "NO_DIFFICULTY": 0.0,
        "SOME_DIFFICULTY": 0.33,
        "A_LOT_OF_DIFFICULTY": 0.67,
        "CANNOT_DO_AT_ALL": 1.0,
    },
}

# Unmet needs are counted, not graded. Five is the number of support
# sub-registers, so a person with an unmet need in every one scores 1.0 here.
_UNMET_NEEDS_CEILING = 5.0


class G2PScoreComputeServiceSupportNeed(G2PScoreComputeInterface):
    @staticmethod
    def _unwrap(value: Any) -> Any:
        return getattr(value, "value", value)

    @classmethod
    def _normalise(cls, key: str, value: Any) -> float:
        """Coerce one contributing attribute onto 0.0 - 1.0."""
        value = cls._unwrap(value)
        if value is None:
            return 0.0

        scale = _ORDINAL_SCALES.get(key)
        if scale is not None:
            return scale.get(str(value).strip().upper(), 0.0)

        if key == "unmet_support_needs_count":
            try:
                return min(float(value) / _UNMET_NEEDS_CEILING, 1.0)
            except (TypeError, ValueError):
                return 0.0

        if isinstance(value, bool):
            return 1.0 if value else 0.0

        try:
            # Numeric contributors are assumed pre-normalised; clamped so a
            # miscalibrated column cannot dominate the whole score.
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return 0.0

    async def compute_score(
        self,
        link_internal_record_id: str,
        contributing_attribute_values: dict,
        score_config: dict,
    ) -> float:
        weights = score_config.get("weights") or {}
        if not isinstance(weights, dict):
            weights = {}

        score = 0.0
        total_weight = 0.0
        for key, weight in weights.items():
            if key not in contributing_attribute_values:
                continue
            try:
                weight = float(weight)
            except (TypeError, ValueError):
                continue
            score += self._normalise(key, contributing_attribute_values.get(key)) * weight
            total_weight += weight

        # Rescale to 0.0 - 1.0 whenever the configured weights do not sum to 1.
        # Without this, adding a contributor in metadata silently shifts every
        # previously computed score, and two deployments with different
        # contributor sets produce numbers that cannot be compared.
        if total_weight > 0:
            score = score / total_weight

        _logger.info(
            "Computed SUPPORT_NEED score %.4f for person %s (attributes=%s)",
            round(score, 4),
            link_internal_record_id,
            sorted(contributing_attribute_values.keys()),
        )
        return round(score, 4)
