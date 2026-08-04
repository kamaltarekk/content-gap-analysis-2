from app.models.domain import ProjectStatus
from app.services.state_machine import can_transition


def test_valid_transition() -> None:
    assert can_transition(ProjectStatus.DRAFT, ProjectStatus.READY_FOR_COLLECTION)


def test_cannot_skip_review() -> None:
    assert not can_transition(ProjectStatus.COLLECTED, ProjectStatus.ANALYZING)
