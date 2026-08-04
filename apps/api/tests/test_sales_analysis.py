import pytest

from app.models.domain import (
    ContentItem,
    EvidenceCategory,
    Evidence,
    FindingStatus,
    PresenceStatus,
)
from app.services.analyzer import (
    MockAnalysisProvider,
    _AIAssessment,
    _AIResponse,
    _persist,
    build_candidates_from_ai,
)
from app.services.repository import repo
from app.services.sales_elements import ELEMENT_IDS
from app.services.scoring import (
    AssessmentCandidate,
    InvalidSalesElementError,
    UnknownEvidenceError,
    build_assessment,
    score_for,
    validate_element,
    validate_evidence_ids,
)

PID = "proj-1"


def _content(entity_id: str, text: str) -> ContentItem:
    return ContentItem(
        project_id=PID,
        entity_id=entity_id,
        source_id="s1",
        url="http://brand.test",
        title="Home",
        text=text,
    )


def _evidence(entity_id: str, category: EvidenceCategory) -> Evidence:
    return Evidence(
        project_id=PID,
        entity_id=entity_id,
        source_id="s1",
        content_item_id="c1",
        verbatim_text="best quality",
        normalized_summary="signal",
        finding_status=FindingStatus.BRAND_CLAIM,
        confidence="low",
        category=category,
    )


# --- scoring rules (unit) ----------------------------------------------------------


def test_se01_blocks_numeric_score() -> None:
    assert score_for("SE01", PresenceStatus.PRESENT) is None
    assert score_for("SE01", PresenceStatus.PARTIAL) is None


def test_unknown_is_not_zero() -> None:
    assert score_for("SE02", PresenceStatus.UNKNOWN) is None
    assert score_for("SE02", PresenceStatus.NOT_APPLICABLE) is None
    # Known presence still scores (absence is a scored low value, distinct from unknown).
    assert score_for("SE02", PresenceStatus.ABSENT_WITHIN_SAMPLE) == 2.0
    assert score_for("SE02", PresenceStatus.PRESENT) == 8.0


def test_validators_reject_unknown_element_and_evidence() -> None:
    with pytest.raises(InvalidSalesElementError):
        validate_element("SE99", "whatever")
    with pytest.raises(InvalidSalesElementError):
        validate_element("SE02", "wrong_key")
    with pytest.raises(UnknownEvidenceError):
        validate_evidence_ids(["missing"], {"real"})


def test_build_assessment_rejects_unknown_evidence() -> None:
    candidate = AssessmentCandidate(
        entity_id="e1",
        canonical_element_id="SE02",
        canonical_key="claim",
        presence_status=PresenceStatus.PRESENT,
        evidence_ids=["ghost"],
    )
    with pytest.raises(UnknownEvidenceError):
        build_assessment(PID, candidate, known_evidence_ids=set())


# --- mock analysis (integration) ---------------------------------------------------


def test_mock_produces_17_canonical_elements_per_entity(temp_db) -> None:
    repo.add(repo.content_items, _content("e1", "premium best quality shipping delivery"))
    assessments, _ = MockAnalysisProvider().analyze(PID)

    ids = sorted(a.canonical_element_id for a in assessments)
    assert ids == sorted(ELEMENT_IDS)
    assert all(a.review_status == "pending_review" for a in assessments)


def test_mock_se01_has_no_score(temp_db) -> None:
    repo.add(repo.content_items, _content("e1", "premium best quality"))
    assessments, _ = MockAnalysisProvider().analyze(PID)
    se01 = next(a for a in assessments if a.canonical_element_id == "SE01")
    assert se01.presence_status == PresenceStatus.UNKNOWN
    assert se01.computed_score is None


def test_mock_unknown_entity_scores_are_none_not_zero(temp_db) -> None:
    # Entity has evidence but no collected content -> every element is unknown.
    repo.add(repo.evidence, _evidence("e-no-content", EvidenceCategory.CLAIM))
    assessments, _ = MockAnalysisProvider().analyze(PID)

    entity = [a for a in assessments if a.entity_id == "e-no-content"]
    non_se01 = [a for a in entity if a.canonical_element_id != "SE01"]
    assert non_se01, "expected assessments for the content-less entity"
    for a in non_se01:
        assert a.presence_status == PresenceStatus.UNKNOWN
        assert a.computed_score is None  # unknown is not zero


def test_mock_evidence_ids_resolve(temp_db) -> None:
    ev = repo.add(repo.evidence, _evidence("e1", EvidenceCategory.CLAIM))
    repo.add(repo.content_items, _content("e1", "premium best quality safe"))
    assessments, _ = MockAnalysisProvider().analyze(PID)

    known = {e.id for e in repo.by_project(repo.evidence, PID)}
    for a in assessments:
        for eid in a.evidence_ids:
            assert eid in known  # every cited evidence id resolves

    se02 = next(a for a in assessments if a.canonical_element_id == "SE02")
    assert ev.id in se02.evidence_ids  # claim evidence links to SE02 (claim)


# --- anthropic adapter finalization (integration) ----------------------------------


def test_ai_candidates_persist_and_validate(temp_db) -> None:
    ev = repo.add(repo.evidence, _evidence("e1", EvidenceCategory.CLAIM))
    response = _AIResponse(
        assessments=[
            _AIAssessment(
                entity_id="e1",
                canonical_element_id="SE02",
                canonical_key="claim",
                presence_status=PresenceStatus.PRESENT,
                evidence_ids=[ev.id],
            ),
            _AIAssessment(
                entity_id="e1",
                canonical_element_id="SE01",
                canonical_key="trigger_pain",
                presence_status=PresenceStatus.UNKNOWN,
            ),
        ]
    )
    assessments = _persist(PID, build_candidates_from_ai(response))

    by_id = {a.canonical_element_id: a for a in assessments}
    assert by_id["SE02"].computed_score == 8.0
    assert by_id["SE01"].computed_score is None  # unresolved element blocks score
    assert all(a.review_status == "pending_review" for a in assessments)


def test_ai_unknown_evidence_id_is_rejected(temp_db) -> None:
    response = _AIResponse(
        assessments=[
            _AIAssessment(
                entity_id="e1",
                canonical_element_id="SE02",
                canonical_key="claim",
                presence_status=PresenceStatus.PRESENT,
                evidence_ids=["not-a-real-id"],
            )
        ]
    )
    with pytest.raises(UnknownEvidenceError):
        _persist(PID, build_candidates_from_ai(response))
