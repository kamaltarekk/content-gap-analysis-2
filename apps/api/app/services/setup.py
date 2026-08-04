from __future__ import annotations

from app.models.domain import Bottleneck, Project, ProjectStatus
from app.services.state_machine import allowed_targets

# Fields a guided setup must supply before a project can leave DRAFT for collection.
# primary_bottleneck is intentionally excluded: "unknown" is a valid, allowed answer
# (domain rule 7 — unknown is not zero), so it never blocks setup.
REQUIRED_SETUP_FIELDS: tuple[str, ...] = (
    "name",
    "brand_name",
    "market",
    "product_or_service",
    "target_buying_decision",
    "purchase_type",
    "primary_segment",
)


def missing_setup_fields(project: Project) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_SETUP_FIELDS:
        value = getattr(project, field, None)
        if value is None or str(value).strip() == "":
            missing.append(field)
    return missing


def is_setup_conditional(project: Project) -> bool:
    """A project is conditional while its primary bottleneck is unresolved.

    Setup may still complete and collection may start, but the unresolved bottleneck
    must remain visible so downstream analysis is not treated as fully grounded.
    """
    return project.primary_bottleneck == Bottleneck.UNKNOWN


def setup_status(project: Project) -> dict:
    missing = missing_setup_fields(project)
    return {
        "status": project.status,
        "missing_fields": missing,
        "ready_for_collection": not missing,
        "bottleneck_resolved": not is_setup_conditional(project),
        "conditional": is_setup_conditional(project),
        "can_submit_setup": (not missing)
        and (ProjectStatus.READY_FOR_COLLECTION in allowed_targets(project.status)),
        "allowed_transitions": sorted(allowed_targets(project.status)),
    }
