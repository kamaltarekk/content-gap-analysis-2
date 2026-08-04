from __future__ import annotations

import json
from abc import ABC, abstractmethod

from anthropic import Anthropic

from app.core.config import settings
from app.models.domain import Evidence, Gap, PresenceStatus, ReviewStatus, SalesElementAssessment
from app.services.repository import repo
from app.services.sales_elements import KEYWORDS, SALES_ELEMENTS


class AnalysisProvider(ABC):
    @abstractmethod
    def analyze(self, project_id: str) -> tuple[list[Evidence], list[SalesElementAssessment], list[Gap]]:
        raise NotImplementedError


class MockAnalysisProvider(AnalysisProvider):
    def analyze(self, project_id: str) -> tuple[list[Evidence], list[SalesElementAssessment], list[Gap]]:
        content = repo.by_project(repo.content_items, project_id)
        by_entity: dict[str, list] = {}
        for item in content:
            by_entity.setdefault(item.entity_id, []).append(item)

        evidence: list[Evidence] = []
        assessments: list[SalesElementAssessment] = []
        gaps: list[Gap] = []

        for entity_id, items in by_entity.items():
            corpus = "\n".join(item.text.lower() for item in items)
            first = items[0]
            for element_id, _family, key in SALES_ELEMENTS:
                if element_id == "SE01":
                    assessment = SalesElementAssessment(
                        project_id=project_id,
                        entity_id=entity_id,
                        canonical_element_id=element_id,
                        canonical_key=key,
                        presence_status=PresenceStatus.UNKNOWN,
                        computed_score=None,
                        confidence="low",
                        recommendation="Resolve Trigger/Pain mapping before scoring.",
                    )
                    repo.add(repo.assessments, assessment)
                    assessments.append(assessment)
                    continue

                matches = [kw for kw in KEYWORDS.get(key, []) if kw.lower() in corpus]
                presence = PresenceStatus.PRESENT if len(matches) >= 2 else PresenceStatus.PARTIAL if matches else PresenceStatus.ABSENT_WITHIN_SAMPLE
                score = 8.0 if presence == PresenceStatus.PRESENT else 4.0 if presence == PresenceStatus.PARTIAL else 1.0
                evidence_ids: list[str] = []
                if matches:
                    ev = Evidence(
                        project_id=project_id,
                        entity_id=entity_id,
                        source_id=first.source_id,
                        content_item_id=first.id,
                        verbatim_text=", ".join(matches[:5]),
                        normalized_summary=f"Keyword signals found for {key}.",
                        finding_status="inference",
                        confidence="low",
                    )
                    repo.add(repo.evidence, ev)
                    evidence.append(ev)
                    evidence_ids.append(ev.id)
                assessment = SalesElementAssessment(
                    project_id=project_id,
                    entity_id=entity_id,
                    canonical_element_id=element_id,
                    canonical_key=key,
                    presence_status=presence,
                    computed_score=score,
                    score_rule_version="mock-keyword-v1",
                    confidence="low",
                    evidence_ids=evidence_ids,
                    recommendation="Human review required; mock analysis is directional only.",
                )
                repo.add(repo.assessments, assessment)
                assessments.append(assessment)

            weak = [a for a in assessments if a.entity_id == entity_id and a.computed_score is not None and a.computed_score < 5]
            for assessment in weak[:3]:
                gap = Gap(
                    project_id=project_id,
                    title=f"Weak {assessment.canonical_key} coverage within collected sample",
                    gap_type="sales_element_gap",
                    status="candidate",
                    severity="medium",
                    confidence="low",
                    root_cause="coverage_gap",
                    evidence_ids=assessment.evidence_ids,
                    alternative_explanations=["Relevant content may exist outside the collected sample."],
                )
                repo.add(repo.gaps, gap)
                gaps.append(gap)

        return evidence, assessments, gaps


class AnthropicAnalysisProvider(AnalysisProvider):
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic analysis")
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def analyze(self, project_id: str) -> tuple[list[Evidence], list[SalesElementAssessment], list[Gap]]:
        # Phase 5: implement strict structured output and evidence-ID validation.
        raise NotImplementedError("Claude Code should implement Phase 5 using strict JSON schemas")


def get_analysis_provider() -> AnalysisProvider:
    if settings.analysis_provider == "anthropic":
        return AnthropicAnalysisProvider()
    return MockAnalysisProvider()
