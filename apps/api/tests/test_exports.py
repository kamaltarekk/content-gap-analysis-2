import json

from bs4 import BeautifulSoup

from app.models.domain import ContentItem, Entity, EntityType, Project
from app.services.analyzer import MockAnalysisProvider
from app.services.artifact import artifact_payload, csv_for, render_artifact_html
from app.services.evidence import extract_candidate_evidence
from app.services.repository import repo

ARABIC = "منتج آمن وبه شهادة جودة"


def _seed() -> str:
    project = repo.add(
        repo.projects,
        Project(
            name="Audit",
            brand_name="Acme",
            market="EG",
            product_or_service="filters",
            target_buying_decision="buy a home filter",
            purchase_type="considered",
            primary_segment="households",
        ),
    )
    brand = repo.add(
        repo.entities, Entity(project_id=project.id, name="Acme", entity_type=EntityType.BRAND)
    )
    repo.add(
        repo.content_items,
        ContentItem(
            project_id=project.id,
            entity_id=brand.id,
            source_id="s1",
            url="http://acme.test/home",
            text="best quality safe reviews testimonials certificate " + ARABIC,
        ),
    )
    extract_candidate_evidence(project.id)
    MockAnalysisProvider().analyze(project.id)
    return project.id


# --- payload integrity -------------------------------------------------------------


def test_counts_resolve(temp_db) -> None:
    pid = _seed()
    payload = artifact_payload(pid)
    assert payload["counts"]["evidence"] == len(repo.by_project(repo.evidence, pid))
    assert payload["counts"]["sales_elements"] == len(repo.by_project(repo.assessments, pid))
    assert payload["counts"]["gaps"] == len(repo.by_project(repo.gaps, pid))
    assert payload["counts"]["content_items"] == 1


def test_all_links_resolve(temp_db) -> None:
    pid = _seed()
    payload = artifact_payload(pid)

    evidence_ids = {e["id"] for e in payload["evidence"]}
    content_urls = {c.url for c in repo.by_project(repo.content_items, pid)}

    # Every evidence row links to a real collected page.
    for e in payload["evidence"]:
        assert e["source_url"] in content_urls

    # Every cited evidence id (on gaps and assessments) resolves to an evidence row.
    for g in payload["gaps"]:
        for eid in g["evidence_ids"]:
            assert eid in evidence_ids
    for a in payload["sales_elements"]:
        for eid in a["evidence_ids"]:
            assert eid in evidence_ids


# --- artifact HTML -----------------------------------------------------------------


def test_artifact_html_has_no_syntax_errors(temp_db) -> None:
    pid = _seed()
    payload = artifact_payload(pid)
    doc = render_artifact_html(payload)

    soup = BeautifulSoup(doc, "html.parser")
    # The embedded data must be valid JSON (the artifact "loads without syntax errors").
    script = soup.find("script", id="artifact-data")
    assert script is not None
    reparsed = json.loads(script.string)
    assert reparsed["counts"] == payload["counts"]

    # Counter tiles in the rendered HTML match the real counts.
    for tile in soup.select("[data-count]"):
        key = tile["data-count"]
        assert int(tile.text) == payload["counts"][key]


def test_artifact_preserves_arabic_and_is_rtl_safe(temp_db) -> None:
    pid = _seed()
    doc = render_artifact_html(artifact_payload(pid))
    assert ARABIC in doc  # Arabic text preserved unchanged (rule: keep AR/EN as-is)
    assert 'dir="auto"' in doc


# --- endpoints + CSV ---------------------------------------------------------------


def test_export_endpoints(client) -> None:
    project = client.post(
        "/api/projects",
        json={
            "name": "Audit",
            "brand_name": "Acme",
            "market": "EG",
            "product_or_service": "filters",
            "target_buying_decision": "buy filter",
            "purchase_type": "considered",
            "primary_segment": "households",
        },
    ).json()
    pid = project["id"]

    assert client.get(f"/api/projects/{pid}/export.json").status_code == 200
    html_resp = client.get(f"/api/projects/{pid}/artifact.html")
    assert html_resp.status_code == 200
    assert html_resp.headers["content-type"].startswith("text/html")

    csv_resp = client.get(f"/api/projects/{pid}/export/gaps.csv")
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert csv_resp.text.splitlines()[0].startswith("id,gap_type")

    assert client.get(f"/api/projects/{pid}/export/nope.csv").status_code == 404
    assert client.get("/api/projects/missing/export.json").status_code == 404


def test_csv_joins_evidence_ids(temp_db) -> None:
    pid = _seed()
    payload = artifact_payload(pid)
    text = csv_for(payload, "sales_elements")
    assert text.splitlines()[0].startswith("entity_id,canonical_element_id")
