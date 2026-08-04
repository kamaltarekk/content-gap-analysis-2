from app.models.domain import Bottleneck, Project, ProjectStatus
from app.services.setup import is_setup_conditional, missing_setup_fields, setup_status

VALID_SETUP = {
    "name": "Acme Audit",
    "brand_name": "Acme",
    "market": "EG",
    "product_or_service": "Water filters",
    "target_buying_decision": "Buy a home water filter",
    "purchase_type": "considered",
    "primary_segment": "households",
}


def _create(client, **overrides):
    body = {**VALID_SETUP, **overrides}
    response = client.post("/api/projects", json=body)
    return response


# --- unit-level validation helpers -------------------------------------------------


def test_missing_setup_fields_detects_blanks() -> None:
    project = Project(**{**VALID_SETUP, "target_buying_decision": "   "})
    assert missing_setup_fields(project) == ["target_buying_decision"]


def test_unknown_bottleneck_is_conditional_but_not_missing() -> None:
    project = Project(**VALID_SETUP, primary_bottleneck=Bottleneck.UNKNOWN)
    # Unknown is allowed: it is never reported as a missing required field...
    assert "primary_bottleneck" not in missing_setup_fields(project)
    # ...but the project is flagged conditional until the bottleneck is resolved.
    assert is_setup_conditional(project) is True


def test_resolved_bottleneck_is_not_conditional() -> None:
    project = Project(**VALID_SETUP, primary_bottleneck=Bottleneck.ATTENTION)
    assert is_setup_conditional(project) is False
    assert setup_status(project)["bottleneck_resolved"] is True


# --- API: strict validation --------------------------------------------------------


def test_create_rejects_unknown_bottleneck_enum_value(client) -> None:
    response = _create(client, primary_bottleneck="banana")
    assert response.status_code == 422


def test_create_rejects_blank_required_field(client) -> None:
    response = _create(client, primary_segment="")
    assert response.status_code == 422


# --- API: unknown bottleneck allowed but conditional -------------------------------


def test_unknown_bottleneck_allows_setup_submission_flagged_conditional(client) -> None:
    project = _create(client, primary_bottleneck="unknown").json()
    assert project["status"] == "DRAFT"

    status = client.get(f"/api/projects/{project['id']}/setup").json()
    assert status["ready_for_collection"] is True
    assert status["conditional"] is True
    assert status["can_submit_setup"] is True

    submitted = client.post(f"/api/projects/{project['id']}/submit-setup")
    assert submitted.status_code == 200
    body = submitted.json()
    assert body["project"]["status"] == "READY_FOR_COLLECTION"
    assert body["conditional"] is True


# --- API: state machine transitions ------------------------------------------------


def test_valid_transition_returns_200(client) -> None:
    project = _create(client).json()
    response = client.post(
        f"/api/projects/{project['id']}/transition",
        json={"target": "READY_FOR_COLLECTION"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "READY_FOR_COLLECTION"


def test_invalid_transition_returns_409(client) -> None:
    project = _create(client).json()
    response = client.post(
        f"/api/projects/{project['id']}/transition",
        json={"target": "ANALYZING"},
    )
    assert response.status_code == 409


def test_transition_to_unknown_status_is_422(client) -> None:
    project = _create(client).json()
    response = client.post(
        f"/api/projects/{project['id']}/transition",
        json={"target": "NOT_A_STATUS"},
    )
    assert response.status_code == 422


def test_setup_edit_blocked_after_leaving_draft(client) -> None:
    project = _create(client).json()
    client.post(
        f"/api/projects/{project['id']}/transition",
        json={"target": "READY_FOR_COLLECTION"},
    )
    response = client.patch(f"/api/projects/{project['id']}", json={"market": "SA"})
    assert response.status_code == 409


def test_patch_updates_setup_fields_while_draft(client) -> None:
    project = _create(client).json()
    response = client.patch(
        f"/api/projects/{project['id']}",
        json={"primary_bottleneck": "friction", "market": "SA"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["primary_bottleneck"] == "friction"
    assert body["market"] == "SA"
    assert body["status"] == "DRAFT"


def test_submit_setup_from_wrong_state_returns_409(client) -> None:
    project = _create(client).json()
    client.post(
        f"/api/projects/{project['id']}/transition",
        json={"target": "READY_FOR_COLLECTION"},
    )
    # Already past DRAFT -> submit-setup is no longer a legal transition.
    response = client.post(f"/api/projects/{project['id']}/submit-setup")
    assert response.status_code == 409


def test_defaults_to_unknown_bottleneck_when_omitted(client) -> None:
    body = {k: v for k, v in VALID_SETUP.items()}
    project = client.post("/api/projects", json=body).json()
    assert project["primary_bottleneck"] == "unknown"
    assert project["status"] == ProjectStatus.DRAFT.value
