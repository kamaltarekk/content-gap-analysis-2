from __future__ import annotations

from app.models.domain import (
    Bottleneck,
    EntityType,
    Gap,
    GapStatus,
    GapType,
    PresenceStatus,
    RootCause,
)
from app.services.comparability import assess_comparability, can_total
from app.services.repository import repo
from app.services.sales_elements import ELEMENT_TO_CATEGORY, FAMILY_BY_ID, KEY_BY_ID, SALES_ELEMENTS

# Severity (impact) is derived from the element family; confidence is derived from evidence
# strength. They are computed by separate functions and never collapsed into one value
# (domain rule 6).
FAMILY_SEVERITY = {"core": "high", "trust": "high", "intellect": "medium", "instinct": "low"}

# Non-content blockers can be suspected from the declared bottleneck, but public content can
# never confirm or deny them (rules 11 and 13). They stay a separate, unconfirmable candidate.
NON_CONTENT_ROOT_CAUSES = {
    RootCause.TRAFFIC,
    RootCause.TARGETING,
    RootCause.PRICING,
    RootCause.LOGISTICS,
    RootCause.TECHNICAL,
}
BOTTLENECK_BLOCKERS: dict[Bottleneck, tuple[RootCause, str]] = {
    Bottleneck.ATTENTION: (RootCause.TRAFFIC, "Attention/traffic is an acquisition blocker, not a content gap."),
    Bottleneck.FRICTION: (RootCause.LOGISTICS, "Friction points are operational blockers, not a content gap."),
}

_COMPETITOR_CAVEATS = [
    "Competitor presence in a limited public sample is not proof of impact.",
    "May reflect sampling differences rather than a real content gap.",
]


def severity_for_element(element_id: str) -> str:
    return FAMILY_SEVERITY.get(FAMILY_BY_ID.get(element_id, ""), "medium")


def confidence_for(evidence_ids: list[str], reviewed: bool) -> str:
    """Confidence reflects how well-grounded the finding is — independent of severity."""
    if reviewed:
        return "high"
    if evidence_ids:
        return "medium"
    return "low"


def _root_cause_for_element(element_id: str) -> RootCause:
    category = ELEMENT_TO_CATEGORY.get(element_id)
    if category == "claim_proof":
        return RootCause.WEAK_CLAIM_PROOF
    if category == "social_proof":
        return RootCause.MISSING_SOCIAL_PROOF
    if FAMILY_BY_ID.get(element_id) in {"intellect", "instinct"}:
        return RootCause.WEAK_PERSUASION
    return RootCause.COVERAGE_GAP


def generate_candidate_gaps(project_id: str) -> list[Gap]:
    project = repo.projects.get(project_id)
    if project is None:
        return []

    entities = repo.by_project(repo.entities, project_id)
    assessments = repo.by_project(repo.assessments, project_id)
    content = repo.by_project(repo.content_items, project_id)

    page_counts: dict[str, int] = {}
    for item in content:
        page_counts[item.entity_id] = page_counts.get(item.entity_id, 0) + 1

    by_entity_element = {(a.entity_id, a.canonical_element_id): a for a in assessments}
    brands = [e for e in entities if e.entity_type == EntityType.BRAND]
    competitors = [e for e in entities if e.entity_type == EntityType.COMPETITOR]

    gaps: list[Gap] = []

    # --- brand content gaps ---
    for brand in brands:
        for element_id, _family, key in SALES_ELEMENTS:
            assessment = by_entity_element.get((brand.id, element_id))
            if assessment is None:
                continue
            if assessment.presence_status not in (
                PresenceStatus.ABSENT_WITHIN_SAMPLE,
                PresenceStatus.PARTIAL,
            ):
                continue
            gaps.append(
                Gap(
                    project_id=project_id,
                    title=f"{key} is thin within the analyzed sample",
                    gap_type=GapType.SALES_ELEMENT_GAP,
                    status=GapStatus.CANDIDATE,
                    severity=severity_for_element(element_id),
                    confidence=confidence_for(assessment.evidence_ids, reviewed=False),
                    root_cause=_root_cause_for_element(element_id),
                    evidence_ids=assessment.evidence_ids,
                    alternative_explanations=[
                        "Relevant content may exist outside the collected sample."
                    ],
                )
            )

    # --- comparative gaps (competitor present, brand absent/unknown) ---
    for brand in brands:
        for element_id, _family, key in SALES_ELEMENTS:
            brand_assessment = by_entity_element.get((brand.id, element_id))
            brand_presence = brand_assessment.presence_status if brand_assessment else PresenceStatus.UNKNOWN
            if brand_presence not in (PresenceStatus.ABSENT_WITHIN_SAMPLE, PresenceStatus.UNKNOWN):
                continue
            for competitor in competitors:
                comp = by_entity_element.get((competitor.id, element_id))
                if comp is None or comp.presence_status != PresenceStatus.PRESENT:
                    continue
                comparable = can_total(assess_comparability(page_counts.get(competitor.id, 0)))
                # Competitor behavior alone can never confirm a gap (rule 14): it stays a
                # probable candidate at best, and only insufficient_evidence when the
                # competitor sample itself is too small to compare.
                status = GapStatus.PROBABLE if comparable else GapStatus.INSUFFICIENT_EVIDENCE
                gaps.append(
                    Gap(
                        project_id=project_id,
                        title=f"{competitor.name} shows {key}; {brand.name} does not within sample",
                        gap_type=GapType.COMPARATIVE_GAP,
                        status=status,
                        severity=severity_for_element(element_id),
                        confidence="low",
                        root_cause=RootCause.COVERAGE_GAP,
                        evidence_ids=comp.evidence_ids,
                        alternative_explanations=list(_COMPETITOR_CAVEATS),
                    )
                )

    # --- non-content blocker candidates (kept separate; never content-confirmable) ---
    blocker = BOTTLENECK_BLOCKERS.get(project.primary_bottleneck)
    if blocker is not None:
        root_cause, note = blocker
        gaps.append(
            Gap(
                project_id=project_id,
                title=f"Declared bottleneck '{project.primary_bottleneck}' suggests a non-content blocker",
                gap_type=GapType.NON_CONTENT_BLOCKER,
                status=GapStatus.NON_CONTENT_BLOCKER_CANDIDATE,
                severity="medium",
                confidence="low",
                root_cause=root_cause,
                evidence_ids=[],
                alternative_explanations=[
                    note,
                    "Cannot be confirmed or denied from public content analysis (rules 11 and 13).",
                ],
            )
        )

    for gap in gaps:
        repo.add(repo.gaps, gap)
    return gaps
