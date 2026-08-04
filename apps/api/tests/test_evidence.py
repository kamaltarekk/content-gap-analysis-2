from app.models.domain import (
    ContentItem,
    EvidenceCategory,
    Evidence,
    FindingStatus,
    ReviewStatus,
)
from app.services.evidence import extract_candidate_evidence, extract_from_content_item
from app.services.repository import repo

SIGNAL_TEXT = (
    "Our premium filter is the best quality and safe. "
    "Read customer reviews and testimonials from happy customers. "
    "See our lab certificate, independent test report, and clinical study."
)


def _content_item(text: str = SIGNAL_TEXT, project_id: str = "p1") -> ContentItem:
    return ContentItem(
        project_id=project_id,
        entity_id="e1",
        source_id="s1",
        url="http://brand.test",
        title="Home",
        text=text,
    )


# --- extraction -------------------------------------------------------------------


def test_extraction_distinguishes_claim_social_and_claim_proof() -> None:
    candidates = extract_from_content_item(_content_item())
    categories = {c.category for c in candidates}
    assert EvidenceCategory.CLAIM in categories
    assert EvidenceCategory.SOCIAL_PROOF in categories
    assert EvidenceCategory.CLAIM_PROOF in categories

    by_cat = {c.category: c for c in candidates}
    assert by_cat[EvidenceCategory.CLAIM].finding_status == FindingStatus.BRAND_CLAIM
    assert by_cat[EvidenceCategory.CLAIM_PROOF].finding_status == FindingStatus.OBSERVED_FACT


def test_extraction_preserves_verbatim_text() -> None:
    candidates = extract_from_content_item(_content_item("منتج آمن وبه شهادة جودة"))
    assert candidates, "expected Arabic signals to be extracted"
    for candidate in candidates:
        assert candidate.verbatim_text in "منتج آمن وبه شهادة جودة"


def test_no_candidate_is_auto_approved(temp_db) -> None:
    repo.add(repo.content_items, _content_item())
    created = extract_candidate_evidence("p1")

    assert created, "expected candidate evidence to be created"
    assert all(e.review_status == ReviewStatus.PENDING for e in created)
    assert all(e.reviewer is None and e.reviewed_at is None for e in created)


def test_extraction_is_idempotent_per_content_item(temp_db) -> None:
    repo.add(repo.content_items, _content_item())
    first = extract_candidate_evidence("p1")
    second = extract_candidate_evidence("p1")

    assert first and second == []
    assert len(repo.by_project(repo.evidence, "p1")) == len(first)


# --- review actions ---------------------------------------------------------------


def _pending_evidence() -> Evidence:
    return repo.add(
        repo.evidence,
        Evidence(
            project_id="p1",
            entity_id="e1",
            source_id="s1",
            content_item_id="c1",
            verbatim_text="the best quality",
            normalized_summary="claim signal",
            finding_status=FindingStatus.BRAND_CLAIM,
            confidence="low",
            category=EvidenceCategory.CLAIM,
        ),
    )


def test_approve_records_reviewer_and_timestamp(client) -> None:
    evidence = _pending_evidence()
    response = client.post(
        f"/api/evidence/{evidence.id}/review",
        json={"status": "approved", "reviewer": "alice"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "approved"
    assert body["reviewer"] == "alice"
    assert body["reviewed_at"] is not None


def test_edit_maps_to_edited_and_approved(client) -> None:
    evidence = _pending_evidence()
    response = client.post(
        f"/api/evidence/{evidence.id}/review",
        json={"status": "approved", "edited_value": "Refined summary", "reviewer": "bob"},
    )
    body = response.json()
    assert body["review_status"] == "edited_and_approved"
    assert body["normalized_summary"] == "Refined summary"
    assert body["reviewer"] == "bob"


def test_reject_and_hypothesis_are_recorded(client) -> None:
    for status in ("rejected", "hypothesis"):
        evidence = _pending_evidence()
        response = client.post(
            f"/api/evidence/{evidence.id}/review",
            json={"status": status, "reviewer": "carol", "note": "context"},
        )
        body = response.json()
        assert body["review_status"] == status
        assert body["reviewer"] == "carol"
        assert body["reviewed_at"] is not None
        assert body["review_note"] == "context"


def test_review_requires_non_empty_reviewer(client) -> None:
    evidence = _pending_evidence()
    response = client.post(
        f"/api/evidence/{evidence.id}/review",
        json={"status": "approved", "reviewer": ""},
    )
    assert response.status_code == 422


VALID_PROJECT = {
    "name": "Acme Audit",
    "brand_name": "Acme",
    "market": "EG",
    "product_or_service": "Water filters",
    "target_buying_decision": "Buy a home water filter",
    "purchase_type": "considered",
    "primary_segment": "households",
}


def test_review_queue_lists_and_filters(client) -> None:
    project = client.post("/api/projects", json=VALID_PROJECT).json()
    pid = project["id"]
    repo.add(repo.content_items, _content_item(project_id=pid))
    extract_candidate_evidence(pid)

    all_items = client.get(f"/api/projects/{pid}/review-queue").json()
    assert len(all_items) > 0
    assert all(item["review_status"] == "pending_review" for item in all_items)

    pending = client.get(
        f"/api/projects/{pid}/review-queue", params={"review_status": "pending_review"}
    ).json()
    assert len(pending) == len(all_items)


def test_prepare_review_extracts_candidates_without_auto_approval(client) -> None:
    project = client.post("/api/projects", json=VALID_PROJECT).json()
    pid = project["id"]
    # Drive the project to COLLECTED so prepare-review is a legal transition.
    for target in ("READY_FOR_COLLECTION", "COLLECTING", "COLLECTED"):
        client.post(f"/api/projects/{pid}/transition", json={"target": target})
    repo.add(repo.content_items, _content_item(project_id=pid))

    response = client.post(f"/api/projects/{pid}/prepare-review")
    assert response.status_code == 200
    assert response.json()["status"] == "READY_FOR_REVIEW"

    queue = client.get(f"/api/projects/{pid}/review-queue").json()
    assert len(queue) > 0
    assert all(item["review_status"] == "pending_review" for item in queue)
