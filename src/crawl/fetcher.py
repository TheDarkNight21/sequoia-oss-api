"""Rate-limited HTTP fetcher for company profile pages."""

from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://sequoiacap.com/companies"
USER_AGENT = "sequoia-oss-api/0.1 (+https://github.com/sequoia-oss-api)"

# Compliance: 1 request per second with jitter
DEFAULT_DELAY = 1.0


def make_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=30,
        follow_redirects=True,
    )


def fetch_company_page(
    slug: str,
    client: httpx.Client,
    delay: float = DEFAULT_DELAY,
) -> str | None:
    """Fetch a single company profile page. Returns HTML or None on failure."""
    url = f"{BASE_URL}/{slug}/"
    try:
        resp = client.get(url)
        resp.raise_for_status()
        time.sleep(delay)
        return resp.text
    except httpx.HTTPStatusError as exc:
        logger.warning("HTTP %s for %s", exc.response.status_code, url)
        time.sleep(delay)
        return None
    except httpx.RequestError as exc:
        logger.warning("Request error for %s: %s", url, exc)
        time.sleep(delay)
        return None


def fetch_pages(
    slugs: list[str],
    client: httpx.Client | None = None,
    delay: float = DEFAULT_DELAY,
) -> dict[str, str]:
    """Fetch multiple company pages. Returns {slug: html} for successful fetches."""
    own_client = client is None
    if own_client:
        client = make_client()
    try:
        results: dict[str, str] = {}
        total = len(slugs)
        for i, slug in enumerate(slugs, 1):
            logger.info("[%d/%d] Fetching %s", i, total, slug)
            html = fetch_company_page(slug, client, delay)
            if html is not None:
                results[slug] = html
        return results
    finally:
        if own_client:
            client.close()
