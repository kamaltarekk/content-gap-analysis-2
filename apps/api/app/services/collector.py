from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.core.config import settings
from app.models.domain import ContentItem, Source, SourceStatus
from app.services.repository import repo


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


async def collect_website(source: Source) -> list[ContentItem]:
    root = str(source.url)
    validate_public_url(root)
    root_host = urlparse(root).netloc
    queue: deque[str] = deque([root])
    visited: set[str] = set()
    items: list[ContentItem] = []
    source.status = SourceStatus.COLLECTING
    source.attempted_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.playwright_headless)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()

        while queue and len(items) < source.max_items:
            url = normalize_url(queue.popleft())
            if url in visited:
                continue
            visited.add(url)
            source.attempted_count += 1
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if response is None or response.status >= 400:
                    source.failed_count += 1
                    continue
                await page.wait_for_timeout(settings.request_delay_ms)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                for node in soup(["script", "style", "noscript", "svg"]):
                    node.decompose()
                text = " ".join(soup.get_text(" ", strip=True).split())
                title = (await page.title()).strip()
                item = ContentItem(
                    project_id=source.project_id,
                    entity_id=source.entity_id,
                    source_id=source.id,
                    url=url,
                    title=title,
                    text=text[:100_000],
                    page_type="webpage",
                    metadata={"http_status": response.status},
                )
                repo.add(repo.content_items, item)
                items.append(item)
                source.accessible_count += 1

                for anchor in soup.find_all("a", href=True):
                    candidate = normalize_url(urljoin(url, anchor["href"]))
                    parsed = urlparse(candidate)
                    if parsed.scheme in {"http", "https"} and parsed.netloc == root_host and candidate not in visited:
                        queue.append(candidate)
            except Exception:
                source.failed_count += 1

        await context.close()
        await browser.close()

    source.discovered_count = len(visited) + len(queue)
    source.status = SourceStatus.COLLECTED if items else SourceStatus.FAILED
    return items
