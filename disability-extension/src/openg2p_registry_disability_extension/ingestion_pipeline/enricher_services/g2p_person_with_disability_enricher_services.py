"""Inbound enrichers for PersonWithDisability.

An enricher runs BEFORE the Jinja template that maps an inbound message onto
registry fields. It exists for the things a template cannot do: look something up
in the database, or reshape a payload whose structure varies between senders.

Field mapping itself belongs in `templates/dci_to_dr_person.json.j2`, not here.
"""

import logging
from typing import Any, Dict, Optional

from openg2p_registry_core.interfaces import G2PPayloadEnricherInterface
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...register_domain.models import G2PRegisterPersonWithDisability

_logger = logging.getLogger("g2p-payload-enricher-service")


def _merge_additional_attributes(raw: Any) -> Dict[str, Any]:
    """DO.DR.02 declares `additional_attributes` as 0...1 object.

    Senders commonly emit a LIST of single-key objects instead. Both shapes are
    accepted and merged into one dict (later keys win), because rejecting the
    list form would fail ingestion on payloads that are otherwise valid.
    """
    merged: Dict[str, Any] = {}
    if isinstance(raw, dict):
        merged.update(raw)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                merged.update(item)
    return merged


def _coerce_self_id_disability(raw: Any) -> Optional[bool]:
    """DO.DR.02 `self_id_disability` is specified as yes (1) / no (0).

    Real senders emit 1/0, "1"/"0", true/false and "yes"/"no". The column is a
    boolean, and an unmapped value must become NULL rather than False — "not
    stated" and "states they are not disabled" are different answers, and
    conflating them undercounts the registry's own target population.
    """
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _resolve_existing_person(
    foundational_id: Optional[str], session: Session
) -> Optional[G2PRegisterPersonWithDisability]:
    if not foundational_id:
        return None
    return session.execute(
        select(G2PRegisterPersonWithDisability).where(
            G2PRegisterPersonWithDisability.foundational_id == str(foundational_id)
        )
    ).scalar_one_or_none()


def _normalise(data: Dict) -> Dict:
    if not isinstance(data, dict):
        return data
    out = dict(data)
    out["additional_attributes"] = _merge_additional_attributes(out.get("additional_attributes"))
    if "self_id_disability" in out:
        out["self_id_disability"] = _coerce_self_id_disability(out.get("self_id_disability"))
    return out


# ── DCI payload enrichers ────────────────────────────────────────────────────


class G2PDciPersonWithDisabilityCreateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciPersonWithDisabilityCreateEnricherService")
        return _normalise(data)


class G2PDciPersonWithDisabilityUpdateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciPersonWithDisabilityUpdateEnricherService")
        return _normalise(data)


class G2PDciPersonWithDisabilityDeleteEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PDciPersonWithDisabilityDeleteEnricherService")
        return data


# ── SPDCI payload enrichers ──────────────────────────────────────────────────


class G2PSpdciPersonWithDisabilityCreateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PSpdciPersonWithDisabilityCreateEnricherService")
        return _normalise(data)


class G2PSpdciPersonWithDisabilityUpdateEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PSpdciPersonWithDisabilityUpdateEnricherService")
        return _normalise(data)


class G2PSpdciPersonWithDisabilityDeleteEnricherService(G2PPayloadEnricherInterface):
    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PSpdciPersonWithDisabilityDeleteEnricherService")
        return data


# ── CRVS enricher ────────────────────────────────────────────────────────────


class G2PCrvsPersonWithDisabilityDeathEnricherService(G2PPayloadEnricherInterface):
    """Attach an inbound CRVS death notification to the person it concerns.

    This is the interface the disability registry most needs from CRVS: without
    it, deceased registrants stay ACTIVE and continue to appear in caseloads and
    in every coverage denominator. The enricher resolves the record; the
    registry's own change-request flow decides what to do with it.
    """

    def enrich(self, data: Dict, session: Session) -> Dict:
        _logger.info("Processing G2PCrvsPersonWithDisabilityDeathEnricherService")
        if not isinstance(data, dict):
            return data

        out = _normalise(data)
        identifier = out.get("foundational_id") or out.get("identifier")
        person = _resolve_existing_person(identifier, session)
        if person is None:
            _logger.warning(
                "CRVS death notification for unknown registrant (identifier=%s) — not ingested",
                identifier,
            )
            raise ValueError("No matching person with disability for CRVS death notification")

        out["internal_record_id"] = person.internal_record_id
        return out
