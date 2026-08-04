from app.models.domain import ProjectStatus

ALLOWED_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.DRAFT: {ProjectStatus.READY_FOR_COLLECTION},
    ProjectStatus.READY_FOR_COLLECTION: {ProjectStatus.COLLECTING},
    ProjectStatus.COLLECTING: {ProjectStatus.COLLECTED, ProjectStatus.FAILED},
    ProjectStatus.COLLECTED: {ProjectStatus.READY_FOR_REVIEW},
    ProjectStatus.READY_FOR_REVIEW: {ProjectStatus.APPROVED_FOR_ANALYSIS},
    ProjectStatus.APPROVED_FOR_ANALYSIS: {ProjectStatus.ANALYZING},
    ProjectStatus.ANALYZING: {ProjectStatus.ANALYZED, ProjectStatus.FAILED},
    ProjectStatus.ANALYZED: {ProjectStatus.READY_FOR_FINAL_REVIEW},
    ProjectStatus.READY_FOR_FINAL_REVIEW: {ProjectStatus.APPROVED},
    ProjectStatus.APPROVED: set(),
    ProjectStatus.FAILED: {ProjectStatus.READY_FOR_COLLECTION},
}


def allowed_targets(current: ProjectStatus) -> set[ProjectStatus]:
    return set(ALLOWED_TRANSITIONS[current])


def can_transition(current: ProjectStatus, target: ProjectStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
