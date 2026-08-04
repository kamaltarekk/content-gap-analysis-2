from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.domain import Gap, PresenceStatus, SalesElementAssessment
from app.services.gaps import generate_candidate_gaps
from app.services.repository import repo
from app.services.sales_elements import (
    ELEMENT_TO_CATEGORY,
    KEYWORDS,
    SALES_ELEMENTS,
    UNRESOLVED_ELEMENTS,
)
from app.services.scoring import AssessmentCandidate, build_assessment


def _known_evidence_ids(project_id: str) -> set[str]:
    return {e.id for e in repo.by_project(repo.evidence, project_id)}


def _persist(
    project_id: str, candidates: list[AssessmentCandidate]
) -> list[SalesElementAssessment]:
    """Validate + persist candidates deterministically (shared by every provider)."""
    known = _known_evidence_ids(project_id)
    assessments: list[SalesElementAssessment] = []
    for candidate in candidates:
        assessment = build_assessment(project_id, candidate, known)
        repo.add(repo.assessments, assessment)
        assessments.append(assessment)
    return assessments


class AnalysisProvider(ABC):
    @abstractmethod
    def analyze(self, project_id: str) -> tuple[list[SalesElementAssessment], list[Gap]]:
        raise NotImplementedError


class MockAnalysisProvider(AnalysisProvider):
    """Deterministic, directional analysis over collected content.

    Presence is inferred from keyword signals; assessments link to already-extracted
    evidence by category so their evidence ids resolve. It never fabricates numeric
    scores where data is absent (unknown stays None) and leaves SE01 unresolved.
    """

    def _candidates(self, project_id: str) -> list[AssessmentCandidate]:
        content = repo.by_project(repo.content_items, project_id)
        entities: dict[str, list] = {}
        for item in content:
            entities.setdefault(item.entity_id, []).append(item)

        evidence = repo.by_project(repo.evidence, project_id)
        evidence_by_entity_category: dict[tuple[str, str], list[str]] = {}
        for e in evidence:
            evidence_by_entity_category.setdefault((e.entity_id, str(e.category)), []).append(e.id)

        # Ensure every entity that has any collected data or evidence is assessed.
        entity_ids = set(entities) | {e.entity_id for e in evidence}

        candidates: list[AssessmentCandidate] = []
        for entity_id in entity_ids:
            items = entities.get(entity_id, [])
            corpus = "\n".join(item.text.lower() for item in items)
            has_content = bool(items)

            for element_id, _family, key in SALES_ELEMENTS:
                if element_id in UNRESOLVED_ELEMENTS:
                    candidates.append(
                        AssessmentCandidate(
                            entity_id=entity_id,
                            canonical_element_id=element_id,
                            canonical_key=key,
                            presence_status=PresenceStatus.UNKNOWN,
                            confidence="low",
                            recommendation="Resolve Trigger/Pain mapping before scoring.",
                        )
                    )
                    continue

                if not has_content:
                    # No data for this entity: unknown, not zero.
                    presence = PresenceStatus.UNKNOWN
                else:
                    matches = [kw for kw in KEYWORDS.get(key, []) if kw.lower() in corpus]
                    presence = (
                        PresenceStatus.PRESENT
                        if len(matches) >= 2
                        else PresenceStatus.PARTIAL
                        if matches
                        else PresenceStatus.ABSENT_WITHIN_SAMPLE
                    )

                category = ELEMENT_TO_CATEGORY.get(element_id)
                evidence_ids = (
                    evidence_by_entity_category.get((entity_id, category), []) if category else []
                )

                candidates.append(
                    AssessmentCandidate(
                        entity_id=entity_id,
                        canonical_element_id=element_id,
                        canonical_key=key,
                        presence_status=presence,
                        confidence="low",
                        evidence_ids=evidence_ids,
                        recommendation="Human review required; mock analysis is directional only.",
                    )
                )
        return candidates

    def analyze(self, project_id: str) -> tuple[list[SalesElementAssessment], list[Gap]]:
        assessments = _persist(project_id, self._candidates(project_id))
        gaps = generate_candidate_gaps(project_id)
        return assessments, gaps


class _AIAssessment(BaseModel):
    entity_id: str
    canonical_element_id: str
    canonical_key: str
    presence_status: PresenceStatus
    confidence: str = "low"
    evidence_ids: list[str] = Field(default_factory=list)
    recommendation: str = ""


class _AIResponse(BaseModel):
    assessments: list[_AIAssessment]


def build_candidates_from_ai(response: _AIResponse) -> list[AssessmentCandidate]:
    return [
        AssessmentCandidate(
            entity_id=a.entity_id,
            canonical_element_id=a.canonical_element_id,
            canonical_key=a.canonical_key,
            presence_status=a.presence_status,
            confidence=a.confidence,
            evidence_ids=a.evidence_ids,
            recommendation=a.recommendation,
        )
        for a in response.assessments
    ]


class AnthropicAnalysisProvider(AnalysisProvider):
    """Anthropic structured-output adapter.

    The model returns strict JSON candidates; the deterministic layer then validates
    enums and evidence ids, applies the score rules, and marks everything pending_review.
    """

    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic analysis")
        from anthropic import Anthropic

        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def _prompt(self, project_id: str) -> tuple[str, str]:
        content = repo.by_project(repo.content_items, project_id)
        evidence = repo.by_project(repo.evidence, project_id)
        element_lines = "\n".join(f"{eid} = {key}" for eid, _fam, key in SALES_ELEMENTS)
        evidence_lines = "\n".join(
            f"- id={e.id} entity={e.entity_id} category={e.category}: {e.verbatim_text}"
            for e in evidence
        )
        content_lines = "\n".join(
            f"[entity={item.entity_id}] {item.title}: {item.text[:2000]}" for item in content
        )
        system = (
            "You classify collected marketing content against the 17 canonical Sales Elements. "
            "Return one assessment per (entity, element). Use only presence values "
            "present, partial, absent_within_sample, unknown, or not_applicable. When there is "
            "no evidence in the sample, use unknown (never invent absence). Keep SE01 unresolved "
            "as unknown. Only cite evidence_ids from the provided list; never invent ids. "
            "Do not assign numeric scores; scoring is applied deterministically downstream."
        )
        user = (
            f"Canonical elements:\n{element_lines}\n\n"
            f"Available evidence (cite ids exactly):\n{evidence_lines or '(none)'}\n\n"
            f"Collected content:\n{content_lines or '(none)'}"
        )
        return system, user

    def analyze(self, project_id: str) -> tuple[list[SalesElementAssessment], list[Gap]]:
        system, user = self._prompt(project_id)
        parsed = self.client.messages.parse(
            model=settings.anthropic_model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=_AIResponse,
        )
        response = parsed.parsed_output
        if response is None:
            raise RuntimeError("Anthropic analysis did not return structured output")
        assessments = _persist(project_id, build_candidates_from_ai(response))
        gaps = generate_candidate_gaps(project_id)
        return assessments, gaps


def get_analysis_provider() -> AnalysisProvider:
    if settings.analysis_provider == "anthropic":
        return AnthropicAnalysisProvider()
    return MockAnalysisProvider()
