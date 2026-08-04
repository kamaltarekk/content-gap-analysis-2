from __future__ import annotations

from dataclasses import dataclass, field

from app.models.domain import PresenceStatus, SalesElementAssessment
from app.services.sales_elements import KEY_BY_ID, UNRESOLVED_ELEMENTS

SCORE_RULE_VERSION = "presence-v1"

# Known presence maps to a numeric score. UNKNOWN and NOT_APPLICABLE deliberately have
# no entry here: unknown is not zero (domain rule 7), so it yields None, not a number.
PRESENCE_SCORE: dict[PresenceStatus, float] = {
    PresenceStatus.PRESENT: 8.0,
    PresenceStatus.PARTIAL: 4.0,
    PresenceStatus.ABSENT_WITHIN_SAMPLE: 2.0,
}


class InvalidSalesElementError(ValueError):
    pass


class UnknownEvidenceError(ValueError):
    pass


def score_for(element_id: str, presence: PresenceStatus) -> float | None:
    """Compute an eligible numeric score, or None when scoring is not warranted.

    Returns None for unresolved elements (SE01 blocks its numeric score, rule 10) and for
    unknown/not-applicable presence (rule 7: unknown is not zero, so it is not scored).
    """
    if element_id in UNRESOLVED_ELEMENTS:
        return None
    if presence in (PresenceStatus.UNKNOWN, PresenceStatus.NOT_APPLICABLE):
        return None
    return PRESENCE_SCORE.get(presence)


def validate_element(element_id: str, canonical_key: str) -> None:
    if element_id not in KEY_BY_ID:
        raise InvalidSalesElementError(f"Unknown canonical element id: {element_id}")
    expected = KEY_BY_ID[element_id]
    if canonical_key != expected:
        raise InvalidSalesElementError(
            f"Canonical key mismatch for {element_id}: expected {expected!r}, got {canonical_key!r}"
        )


def validate_evidence_ids(evidence_ids: list[str], known_ids: set[str]) -> None:
    missing = [eid for eid in evidence_ids if eid not in known_ids]
    if missing:
        raise UnknownEvidenceError(f"Assessment references unknown evidence ids: {missing}")


@dataclass
class AssessmentCandidate:
    """Provider-agnostic candidate; the deterministic layer turns it into a real assessment."""

    entity_id: str
    canonical_element_id: str
    canonical_key: str
    presence_status: PresenceStatus
    confidence: str = "low"
    evidence_ids: list[str] = field(default_factory=list)
    recommendation: str = ""


def build_assessment(
    project_id: str, candidate: AssessmentCandidate, known_evidence_ids: set[str]
) -> SalesElementAssessment:
    """Validate a candidate and produce a pending_review assessment with a scored-or-None result.

    Enforces canonical SE ids/keys, rejects unknown evidence ids (they must resolve), applies
    the score-eligibility rules, and never auto-approves (rule 4).
    """
    validate_element(candidate.canonical_element_id, candidate.canonical_key)
    validate_evidence_ids(candidate.evidence_ids, known_evidence_ids)

    presence = PresenceStatus(candidate.presence_status)
    computed_score = score_for(candidate.canonical_element_id, presence)

    return SalesElementAssessment(
        project_id=project_id,
        entity_id=candidate.entity_id,
        canonical_element_id=candidate.canonical_element_id,
        canonical_key=candidate.canonical_key,
        presence_status=presence,
        computed_score=computed_score,
        score_rule_version=SCORE_RULE_VERSION if computed_score is not None else None,
        confidence=candidate.confidence,
        evidence_ids=list(candidate.evidence_ids),
        recommendation=candidate.recommendation,
    )
