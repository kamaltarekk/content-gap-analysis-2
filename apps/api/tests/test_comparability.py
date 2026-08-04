from app.models.domain import ComparableStatus, ContentItem, Entity, EntityType
from app.services.analyzer import MockAnalysisProvider
from app.services.comparability import assess_comparability, can_total, comparison_matrix
from app.services.repository import repo

PID = "proj-1"
RICH_TEXT = "premium best quality safe reviews testimonials certificate study shipping delivery"


def _entity(entity_id: str, entity_type: EntityType = EntityType.COMPETITOR) -> Entity:
    ent = Entity(id=entity_id, project_id=PID, name=entity_id, entity_type=entity_type)
    return repo.add(repo.entities, ent)


def _content(entity_id: str, url: str) -> None:
    repo.add(
        repo.content_items,
        ContentItem(project_id=PID, entity_id=entity_id, source_id="s1", url=url, text=RICH_TEXT),
    )


# --- thresholds (unit) -------------------------------------------------------------


def test_threshold_blocks_single_page() -> None:
    assert assess_comparability(0) == ComparableStatus.INSUFFICIENT_SAMPLE
    assert assess_comparability(1) == ComparableStatus.INSUFFICIENT_SAMPLE
    assert assess_comparability(3) == ComparableStatus.COMPARABLE


def test_can_total_only_when_comparable() -> None:
    assert can_total(ComparableStatus.COMPARABLE) is True
    assert can_total(ComparableStatus.INSUFFICIENT_SAMPLE) is False
    assert can_total(ComparableStatus.PROVISIONALLY_COMPARABLE) is False


# --- matrix (integration) ----------------------------------------------------------


def test_one_homepage_cannot_receive_total(temp_db) -> None:
    _entity("solo")
    _content("solo", "http://solo.test")  # a single homepage
    MockAnalysisProvider().analyze(PID)

    matrix = comparison_matrix(PID)
    row = next(r for r in matrix["entities"] if r["entity_id"] == "solo")

    assert row["page_count"] == 1
    assert row["comparable_status"] == ComparableStatus.INSUFFICIENT_SAMPLE
    assert row["total"] is None
    assert "homepage" in row["total_blocked_reason"]


def test_comparable_entity_receives_total(temp_db) -> None:
    _entity("deep")
    for i in range(3):
        _content("deep", f"http://deep.test/{i}")
    MockAnalysisProvider().analyze(PID)

    matrix = comparison_matrix(PID)
    row = next(r for r in matrix["entities"] if r["entity_id"] == "deep")

    assert row["page_count"] == 3
    assert row["comparable_status"] == ComparableStatus.COMPARABLE
    assert row["total"] is not None and row["total"] > 0
    assert row["total_blocked_reason"] is None


def test_absence_cells_use_sample_wording(temp_db) -> None:
    _entity("deep")
    for i in range(3):
        # Text with no persuasion signals -> elements read as absent_within_sample.
        repo.add(
            repo.content_items,
            ContentItem(
                project_id=PID,
                entity_id="deep",
                source_id="s1",
                url=f"http://deep.test/{i}",
                text="lorem ipsum plain text with no marketing signals",
            ),
        )
    MockAnalysisProvider().analyze(PID)

    matrix = comparison_matrix(PID)
    row = next(r for r in matrix["entities"] if r["entity_id"] == "deep")
    notes = [cell["note"] for cell in row["cells"].values() if cell["note"]]
    assert notes, "expected at least one absence note"
    assert all(note == "not found within the analyzed sample" for note in notes)
