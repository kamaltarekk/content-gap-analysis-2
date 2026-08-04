from __future__ import annotations

from app.core.config import settings
from app.models.domain import ComparableStatus, PresenceStatus
from app.services.repository import repo
from app.services.sales_elements import SALES_ELEMENTS

# Rule 5: a competitor absence is only ever "not found within the analyzed sample".
ABSENCE_NOTE = "not found within the analyzed sample"

# Rule 12: a single homepage can never be called comparable, so its total is blocked.
INSUFFICIENT_SAMPLE_REASON = (
    "Insufficient sample: a total requires at least "
    f"{settings.comparability_min_pages} collected pages; one homepage cannot receive a total score."
)


def assess_comparability(page_count: int) -> ComparableStatus:
    if page_count < settings.comparability_min_pages:
        return ComparableStatus.INSUFFICIENT_SAMPLE
    return ComparableStatus.COMPARABLE


def can_total(status: ComparableStatus) -> bool:
    return status == ComparableStatus.COMPARABLE


def comparison_matrix(project_id: str) -> dict:
    entities = repo.by_project(repo.entities, project_id)
    content = repo.by_project(repo.content_items, project_id)
    assessments = repo.by_project(repo.assessments, project_id)

    page_counts: dict[str, int] = {}
    for item in content:
        page_counts[item.entity_id] = page_counts.get(item.entity_id, 0) + 1

    by_entity_element: dict[tuple[str, str], object] = {}
    for a in assessments:
        by_entity_element[(a.entity_id, a.canonical_element_id)] = a

    elements = [
        {"canonical_element_id": eid, "canonical_key": key, "family": family}
        for eid, family, key in SALES_ELEMENTS
    ]

    rows = []
    for entity in entities:
        page_count = page_counts.get(entity.id, 0)
        status = assess_comparability(page_count)

        cells: dict[str, dict] = {}
        scored_sum = 0.0
        for eid, _family, _key in SALES_ELEMENTS:
            assessment = by_entity_element.get((entity.id, eid))
            if assessment is None:
                cells[eid] = {"presence_status": None, "computed_score": None, "note": None}
                continue
            presence = assessment.presence_status
            score = assessment.computed_score
            if score is not None:
                scored_sum += score
            note = ABSENCE_NOTE if presence == PresenceStatus.ABSENT_WITHIN_SAMPLE else None
            cells[eid] = {
                "presence_status": presence,
                "computed_score": score,
                "note": note,
            }

        totalable = can_total(status)
        rows.append(
            {
                "entity_id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "page_count": page_count,
                "comparable_status": status,
                "cells": cells,
                "total": scored_sum if totalable else None,
                "total_blocked_reason": None if totalable else INSUFFICIENT_SAMPLE_REASON,
            }
        )

    return {"elements": elements, "entities": rows, "min_pages": settings.comparability_min_pages}
