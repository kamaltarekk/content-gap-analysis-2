from app.models.domain import (
    Bottleneck,
    ContentItem,
    Entity,
    EntityType,
    Gap,
    GapStatus,
    GapType,
    Project,
    RootCause,
)
from app.services.analyzer import MockAnalysisProvider
from app.services.gaps import generate_candidate_gaps
from app.services.repository import repo

BRAND_TEXT = "best quality safe product"  # claim present, no social proof
COMP_TEXT = "great reviews testimonials from happy customers"  # social proof present


def _project(bottleneck: Bottleneck = Bottleneck.UNKNOWN) -> Project:
    return repo.add(
        repo.projects,
        Project(
            name="Audit",
            brand_name="Acme",
            market="EG",
            product_or_service="filters",
            target_buying_decision="buy filter",
            purchase_type="considered",
            primary_segment="households",
            primary_bottleneck=bottleneck,
        ),
    )


def _entity(pid: str, name: str, kind: EntityType) -> Entity:
    return repo.add(repo.entities, Entity(project_id=pid, name=name, entity_type=kind))


def _content(pid: str, entity_id: str, url: str, text: str) -> None:
    repo.add(
        repo.content_items,
        ContentItem(project_id=pid, entity_id=entity_id, source_id="s", url=url, text=text),
    )


def _setup_brand_vs_competitor(pid: str, competitor_pages: int) -> None:
    brand = _entity(pid, "Acme", EntityType.BRAND)
    comp = _entity(pid, "Rival", EntityType.COMPETITOR)
    _content(pid, brand.id, "http://acme.test", BRAND_TEXT)
    for i in range(competitor_pages):
        _content(pid, comp.id, f"http://rival.test/{i}", COMP_TEXT)
    MockAnalysisProvider().analyze(pid)


# --- competitor behavior alone cannot confirm a gap --------------------------------


def test_comparative_gaps_are_never_confirmed(temp_db) -> None:
    project = _project()
    _setup_brand_vs_competitor(project.id, competitor_pages=3)

    gaps = repo.by_project(repo.gaps, project.id)
    comparative = [g for g in gaps if g.gap_type == GapType.COMPARATIVE_GAP]

    assert comparative, "expected a competitor-vs-brand comparative gap"
    for g in comparative:
        assert g.status != GapStatus.CONFIRMED
        assert g.status in (GapStatus.PROBABLE, GapStatus.INSUFFICIENT_EVIDENCE)
        assert g.review_status == "pending_review"
        assert g.alternative_explanations  # carries the "not proof of impact" caveats


def test_comparable_competitor_yields_probable(temp_db) -> None:
    project = _project()
    _setup_brand_vs_competitor(project.id, competitor_pages=3)
    comparative = [g for g in repo.by_project(repo.gaps, project.id) if g.gap_type == GapType.COMPARATIVE_GAP]
    assert any(g.status == GapStatus.PROBABLE for g in comparative)


def test_single_page_competitor_is_insufficient_evidence(temp_db) -> None:
    project = _project()
    _setup_brand_vs_competitor(project.id, competitor_pages=1)
    comparative = [g for g in repo.by_project(repo.gaps, project.id) if g.gap_type == GapType.COMPARATIVE_GAP]
    assert comparative
    assert all(g.status == GapStatus.INSUFFICIENT_EVIDENCE for g in comparative)


# --- non-content blockers remain separate ------------------------------------------


def test_non_content_blocker_is_separate_and_unconfirmed(temp_db) -> None:
    project = _project(bottleneck=Bottleneck.FRICTION)
    brand = _entity(project.id, "Acme", EntityType.BRAND)
    _content(project.id, brand.id, "http://acme.test", BRAND_TEXT)
    MockAnalysisProvider().analyze(project.id)

    gaps = repo.by_project(repo.gaps, project.id)
    blockers = [g for g in gaps if g.gap_type == GapType.NON_CONTENT_BLOCKER]

    assert len(blockers) == 1
    blocker = blockers[0]
    assert blocker.status == GapStatus.NON_CONTENT_BLOCKER_CANDIDATE
    assert blocker.root_cause == RootCause.LOGISTICS
    assert blocker.status != GapStatus.CONFIRMED
    # It is not mixed in with content gaps.
    content_gaps = [g for g in gaps if g.gap_type == GapType.SALES_ELEMENT_GAP]
    assert all(g.gap_type != GapType.NON_CONTENT_BLOCKER for g in content_gaps)


def test_unknown_bottleneck_emits_no_blocker(temp_db) -> None:
    project = _project(bottleneck=Bottleneck.UNKNOWN)
    brand = _entity(project.id, "Acme", EntityType.BRAND)
    _content(project.id, brand.id, "http://acme.test", BRAND_TEXT)
    generate_candidate_gaps(project.id)
    gaps = repo.by_project(repo.gaps, project.id)
    assert not [g for g in gaps if g.gap_type == GapType.NON_CONTENT_BLOCKER]


# --- severity and confidence are separate ------------------------------------------


def test_severity_and_confidence_are_independent(temp_db) -> None:
    project = _project()
    brand = _entity(project.id, "Acme", EntityType.BRAND)
    _content(project.id, brand.id, "http://acme.test", BRAND_TEXT)  # no social proof
    MockAnalysisProvider().analyze(project.id)

    gaps = repo.by_project(repo.gaps, project.id)
    # social_proof (SE09) is a trust-family element -> high severity; no evidence -> low confidence.
    social = [g for g in gaps if "social_proof" in g.title and g.gap_type == GapType.SALES_ELEMENT_GAP]
    assert social
    assert social[0].severity == "high"
    assert social[0].confidence == "low"


# --- confirmation requires a recorded review decision (rule 14) --------------------


def test_gap_confirmation_requires_review(client) -> None:
    gap = repo.add(
        repo.gaps,
        Gap(
            project_id="p1",
            title="comparative candidate",
            gap_type=GapType.COMPARATIVE_GAP,
            status=GapStatus.PROBABLE,
        ),
    )
    response = client.post(
        f"/api/gaps/{gap.id}/review",
        json={"status": "confirmed", "reviewer": "alice", "note": "validated offline"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["reviewer"] == "alice"
    assert body["reviewed_at"] is not None
    assert body["review_status"] == "approved"


def test_gap_review_requires_non_empty_reviewer(client) -> None:
    gap = repo.add(
        repo.gaps,
        Gap(project_id="p1", title="x", gap_type=GapType.SALES_ELEMENT_GAP),
    )
    response = client.post(f"/api/gaps/{gap.id}/review", json={"status": "rejected", "reviewer": ""})
    assert response.status_code == 422
