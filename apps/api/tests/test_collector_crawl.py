import asyncio
import json

from app.models.domain import Source, SourceStatus, SourceType
from app.services.collector import (
    FetchResult,
    PageFetcher,
    collect_website_report,
    collection_log_key,
    normalize_url,
    validate_public_url,
)
from app.services.storage import LocalStorage


class FakeFetcher(PageFetcher):
    """Serves canned pages so crawling is deterministic without a browser or network."""

    def __init__(self, pages: dict[str, FetchResult]) -> None:
        self.pages = pages
        self.fetched: list[str] = []

    async def fetch(self, url: str) -> FetchResult:
        self.fetched.append(url)
        result = self.pages.get(url)
        if result is None:
            return FetchResult(url=url, status=404, error="not found")
        return result


def _page(url: str, html: str = "", status: int = 200) -> FetchResult:
    return FetchResult(url=url, status=status, html=html, title="t", screenshot=b"png")


def _source(url: str, max_items: int = 20) -> Source:
    return Source(
        project_id="p1",
        entity_id="e1",
        source_type=SourceType.WEBSITE,
        url=url,
        max_items=max_items,
    )


def _run(source, fetcher, tmp_path, validate=lambda url: None):
    storage = LocalStorage(tmp_path)
    report = asyncio.run(
        collect_website_report(source, fetcher=fetcher, validate=validate, storage=storage)
    )
    return report, storage


ROOT = "http://brand.test"


def test_cap_is_enforced(temp_db, tmp_path) -> None:
    pages = {
        ROOT: _page(ROOT, '<a href="/a">a</a><a href="/b">b</a><a href="/c">c</a>'),
        f"{ROOT}/a": _page(f"{ROOT}/a"),
        f"{ROOT}/b": _page(f"{ROOT}/b"),
        f"{ROOT}/c": _page(f"{ROOT}/c"),
    }
    fetcher = FakeFetcher(pages)
    report, _ = _run(_source(ROOT, max_items=2), fetcher, tmp_path)

    assert len(report.items) == 2
    assert report.accessible == 2
    # Pages beyond the cap are recorded as skipped, not silently dropped.
    assert any(entry["outcome"] == "skipped_cap" for entry in report.log)


def test_exact_url_preserved(temp_db, tmp_path) -> None:
    fetcher = FakeFetcher({ROOT: _page(ROOT)})
    source = _source(ROOT)
    report, _ = _run(source, fetcher, tmp_path)

    assert report.items[0].url == normalize_url(str(source.url)) == ROOT
    # The exact source URL is never mutated to a different entity.
    assert str(source.url).startswith("http://brand.test")


def test_same_origin_only(temp_db, tmp_path) -> None:
    pages = {
        ROOT: _page(ROOT, '<a href="/a">a</a><a href="http://evil.test/x">x</a>'),
        f"{ROOT}/a": _page(f"{ROOT}/a"),
    }
    fetcher = FakeFetcher(pages)
    report, _ = _run(_source(ROOT), fetcher, tmp_path)

    assert not any("evil.test" in url for url in fetcher.fetched)
    assert all(item.url.startswith(ROOT) for item in report.items)


def test_blocked_status_preserved(temp_db, tmp_path) -> None:
    source = _source("http://127.0.0.1")
    # Use the real validator: a loopback root must be blocked, not crawled.
    report, storage = _run(source, FakeFetcher({}), tmp_path, validate=validate_public_url)

    assert source.status == SourceStatus.BLOCKED
    assert report.final_status == SourceStatus.BLOCKED
    assert report.items == []
    log = json.loads(storage.read_text(collection_log_key(source)))
    assert log[0]["outcome"] == "blocked"


def test_failed_status_when_nothing_accessible(temp_db, tmp_path) -> None:
    fetcher = FakeFetcher({ROOT: FetchResult(url=ROOT, status=500, error="server error")})
    source = _source(ROOT)
    report, _ = _run(source, fetcher, tmp_path)

    assert source.status == SourceStatus.FAILED
    assert report.accessible == 0
    assert source.attempted_count == 1


def test_partial_status_when_some_pages_fail(temp_db, tmp_path) -> None:
    pages = {
        ROOT: _page(ROOT, '<a href="/a">a</a>'),
        f"{ROOT}/a": FetchResult(url=f"{ROOT}/a", status=503, error="unavailable"),
    }
    source = _source(ROOT)
    report, _ = _run(source, FakeFetcher(pages), tmp_path)

    assert source.status == SourceStatus.PARTIAL
    assert report.accessible == 1
    assert report.failed == 1


def test_snapshot_screenshot_and_log_persisted(temp_db, tmp_path) -> None:
    fetcher = FakeFetcher({ROOT: _page(ROOT, "<p>hello</p>")})
    source = _source(ROOT)
    report, storage = _run(source, fetcher, tmp_path)

    meta = report.items[0].metadata
    assert storage.exists(meta["snapshot_key"])
    assert storage.exists(meta["screenshot_key"])

    log = json.loads(storage.read_text(collection_log_key(source)))
    assert log[0]["outcome"] == "collected"
    assert log[0]["http_status"] == 200
