from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.domain import ContentItem, Source, SourceStatus, now_iso
from app.services.repository import repo
from app.services.storage import LocalStorage, default_storage


class UnsafeUrlError(ValueError):
    pass


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("Only public HTTP(S) URLs are allowed")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError("Hostname could not be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UnsafeUrlError("Private or reserved network targets are blocked")


def normalize_url(url: str) -> str:
    clean, _ = urldefrag(url)
    return clean.rstrip("/") or clean


Validator = Callable[[str], None]


@dataclass
class FetchResult:
    """Outcome of fetching a single URL, independent of the browser implementation."""

    url: str
    status: int
    html: str = ""
    title: str = ""
    screenshot: bytes | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and 200 <= self.status < 400


class PageFetcher(ABC):
    """Adapter seam for browser collection so crawling is testable without Playwright."""

    async def start(self) -> None:  # pragma: no cover - default no-op
        return None

    async def stop(self) -> None:  # pragma: no cover - default no-op
        return None

    @abstractmethod
    async def fetch(self, url: str) -> FetchResult:
        raise NotImplementedError


class PlaywrightFetcher(PageFetcher):
    """Real browser fetcher. Imported lazily so the module loads without browsers."""

    def __init__(self, headless: bool | None = None) -> None:
        self.headless = settings.playwright_headless if headless is None else headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(locale="en-US")
        self._page = await self._context.new_page()

    async def stop(self) -> None:
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def fetch(self, url: str) -> FetchResult:
        assert self._page is not None, "PlaywrightFetcher.start() must be called first"
        try:
            response = await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if response is None:
                return FetchResult(url=url, status=0, error="No response")
            await self._page.wait_for_timeout(settings.request_delay_ms)
            html = await self._page.content()
            title = (await self._page.title()).strip()
            screenshot = await self._page.screenshot(full_page=True)
            return FetchResult(
                url=url, status=response.status, html=html, title=title, screenshot=screenshot
            )
        except Exception as exc:  # pragma: no cover - exercised via injected fetchers
            return FetchResult(url=url, status=0, error=str(exc))


def _slug(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _prefix(source: Source) -> str:
    return f"raw/{source.project_id}/{source.id}"


def collection_log_key(source: Source) -> str:
    return f"{_prefix(source)}/collection_log.json"


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _same_origin_links(html: str, base_url: str, root_host: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        candidate = normalize_url(urljoin(base_url, anchor["href"]))
        parsed = urlparse(candidate)
        if parsed.scheme in {"http", "https"} and parsed.netloc == root_host:
            links.append(candidate)
    return links


@dataclass
class CollectionReport:
    source_id: str
    final_status: SourceStatus
    attempted: int = 0
    accessible: int = 0
    failed: int = 0
    items: list[ContentItem] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    log_key: str | None = None


async def collect_website(
    source: Source,
    *,
    fetcher: PageFetcher | None = None,
    validate: Validator = validate_public_url,
    storage: LocalStorage | None = None,
) -> list[ContentItem]:
    """Crawl a source's exact URL and same-origin pages under a hard cap.

    Seams (`fetcher`, `validate`, `storage`) are injectable so collection is testable
    without a real browser or network. Snapshots, screenshots, and a per-URL JSON log
    are written to storage; the source's status and counts reflect the outcome and are
    preserved for the caller to persist.
    """
    report = await _collect(source, fetcher=fetcher, validate=validate, storage=storage)
    return report.items


async def collect_website_report(
    source: Source,
    *,
    fetcher: PageFetcher | None = None,
    validate: Validator = validate_public_url,
    storage: LocalStorage | None = None,
) -> CollectionReport:
    return await _collect(source, fetcher=fetcher, validate=validate, storage=storage)


async def _collect(
    source: Source,
    *,
    fetcher: PageFetcher | None,
    validate: Validator,
    storage: LocalStorage | None,
) -> CollectionReport:
    store = storage or default_storage
    root = normalize_url(str(source.url))
    log: list[dict] = []

    # Exact-URL safety gate: an unsafe root is blocked, never silently substituted.
    try:
        validate(root)
    except UnsafeUrlError as exc:
        source.status = SourceStatus.BLOCKED
        source.attempted_count = 0
        log.append({"url": root, "outcome": "blocked", "error": str(exc), "at": now_iso()})
        report = CollectionReport(source_id=source.id, final_status=SourceStatus.BLOCKED, log=log)
        report.log_key = store.write_text(collection_log_key(source), json.dumps(log, ensure_ascii=False))
        return report

    cap = max(1, min(source.max_items, settings.max_pages_per_source))
    root_host = urlparse(root).netloc

    fetcher = fetcher or PlaywrightFetcher()
    source.status = SourceStatus.COLLECTING
    source.attempted_count = 0
    source.accessible_count = 0
    source.failed_count = 0

    queue: deque[str] = deque([root])
    visited: set[str] = set()
    items: list[ContentItem] = []
    failed = 0

    await fetcher.start()
    try:
        while queue and len(items) < cap:
            url = normalize_url(queue.popleft())
            if url in visited:
                continue
            visited.add(url)
            source.attempted_count += 1

            result = await fetcher.fetch(url)
            if not result.ok:
                failed += 1
                log.append(
                    {
                        "url": url,
                        "outcome": "failed",
                        "http_status": result.status,
                        "error": result.error,
                        "at": now_iso(),
                    }
                )
                continue

            slug = _slug(url)
            snapshot_key = store.write_text(f"{_prefix(source)}/pages/{slug}.html", result.html)
            screenshot_key = None
            if result.screenshot is not None:
                screenshot_key = store.write_bytes(
                    f"{_prefix(source)}/pages/{slug}.png", result.screenshot
                )

            item = ContentItem(
                project_id=source.project_id,
                entity_id=source.entity_id,
                source_id=source.id,
                url=url,  # exact fetched URL, preserved verbatim
                title=result.title,
                text=_extract_text(result.html)[:100_000],
                page_type="webpage",
                metadata={
                    "http_status": result.status,
                    "snapshot_key": snapshot_key,
                    "screenshot_key": screenshot_key,
                },
            )
            repo.add(repo.content_items, item)
            items.append(item)
            source.accessible_count += 1
            log.append(
                {
                    "url": url,
                    "outcome": "collected",
                    "http_status": result.status,
                    "snapshot_key": snapshot_key,
                    "screenshot_key": screenshot_key,
                    "at": now_iso(),
                }
            )

            for candidate in _same_origin_links(result.html, url, root_host):
                if candidate not in visited:
                    queue.append(candidate)

        # Anything still queued when the cap is hit is recorded, not silently dropped.
        if queue and len(items) >= cap:
            for skipped in list(queue):
                log.append({"url": skipped, "outcome": "skipped_cap", "at": now_iso()})
    finally:
        await fetcher.stop()

    source.failed_count = failed
    source.discovered_count = len(visited) + len(queue)
    if items and failed == 0:
        source.status = SourceStatus.COLLECTED
    elif items:
        source.status = SourceStatus.PARTIAL
    else:
        source.status = SourceStatus.FAILED

    report = CollectionReport(
        source_id=source.id,
        final_status=source.status,
        attempted=source.attempted_count,
        accessible=source.accessible_count,
        failed=source.failed_count,
        items=items,
        log=log,
    )
    report.log_key = store.write_text(collection_log_key(source), json.dumps(log, ensure_ascii=False))
    return report
