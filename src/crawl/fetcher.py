"""Rate-limited HTTP fetcher with jitter, retries, and caching."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://sequoiacap.com/companies"
USER_AGENT = "sequoia-oss-api/0.1 (+https://github.com/sequoia-oss-api)"

# Compliance: 1 request per second with jitter
DEFAULT_DELAY = 1.0
DEFAULT_JITTER = 0.3  # +-30% jitter

# Retry config
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds, doubles each retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Cache
DEFAULT_CACHE_DIR = ".cache"


def make_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=30,
        follow_redirects=True,
    )


def _delay_with_jitter(delay: float, jitter: float = DEFAULT_JITTER) -> None:
    actual = delay * (1 + random.uniform(-jitter, jitter))
    time.sleep(max(0.1, actual))


class ContentCache:
    """Stores content hashes per URL to detect changes across runs."""

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self._hash_file = os.path.join(cache_dir, "content_hashes.json")
        self._html_dir = os.path.join(cache_dir, "html")
        self._hashes: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._hash_file):
            with open(self._hash_file) as f:
                self._hashes = json.load(f)

    def save(self) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(self._hash_file, "w") as f:
            json.dump(self._hashes, f, indent=2)
            f.write("\n")

    def has_unchanged(self, slug: str, html: str) -> bool:
        """Check if content hash matches the cached version."""
        new_hash = hashlib.sha256(html.encode()).hexdigest()
        return self._hashes.get(slug) == new_hash

    def update(self, slug: str, html: str) -> None:
        """Store the content hash and cache the HTML."""
        self._hashes[slug] = hashlib.sha256(html.encode()).hexdigest()
        os.makedirs(self._html_dir, exist_ok=True)
        with open(os.path.join(self._html_dir, f"{slug}.html"), "w") as f:
            f.write(html)

    def get_cached_html(self, slug: str) -> str | None:
        """Return cached HTML if available."""
        path = os.path.join(self._html_dir, f"{slug}.html")
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        return None


def fetch_company_page(
    slug: str,
    client: httpx.Client,
    delay: float = DEFAULT_DELAY,
) -> str | None:
    """Fetch a single company profile page with retries. Returns HTML or None."""
    url = f"{BASE_URL}/{slug}/"

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.get(url)
            resp.raise_for_status()
            _delay_with_jitter(delay)
            return resp.text
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                backoff = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "HTTP %s for %s, retrying in %.1fs (attempt %d/%d)",
                    status, url, backoff, attempt + 1, MAX_RETRIES,
                )
                time.sleep(backoff)
                continue
            logger.warning("HTTP %s for %s (giving up)", status, url)
            _delay_with_jitter(delay)
            return None
        except httpx.RequestError as exc:
            if attempt < MAX_RETRIES:
                backoff = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "Request error for %s: %s, retrying in %.1fs",
                    url, exc, backoff,
                )
                time.sleep(backoff)
                continue
            logger.warning("Request error for %s: %s (giving up)", url, exc)
            _delay_with_jitter(delay)
            return None

    return None


def fetch_pages(
    slugs: list[str],
    client: httpx.Client | None = None,
    delay: float = DEFAULT_DELAY,
    cache: ContentCache | None = None,
) -> dict[str, str]:
    """Fetch multiple company pages. Returns {slug: html}.

    Uses cache to skip unchanged pages when provided.
    """
    own_client = client is None
    if own_client:
        client = make_client()
    try:
        results: dict[str, str] = {}
        total = len(slugs)
        cached_count = 0
        fetched_count = 0

        for i, slug in enumerate(slugs, 1):
            # Check cache first
            if cache is not None:
                cached_html = cache.get_cached_html(slug)
                if cached_html is not None:
                    # Verify we have a hash — if so, reuse cached version
                    if cache._hashes.get(slug):
                        results[slug] = cached_html
                        cached_count += 1
                        logger.debug("[%d/%d] Cache hit for %s", i, total, slug)
                        continue

            logger.info("[%d/%d] Fetching %s", i, total, slug)
            html = fetch_company_page(slug, client, delay)
            if html is not None:
                results[slug] = html
                fetched_count += 1
                if cache is not None:
                    cache.update(slug, html)

        if cache is not None:
            cache.save()

        logger.info(
            "Fetch complete: %d fetched, %d from cache, %d total",
            fetched_count, cached_count, len(results),
        )
        return results
    finally:
        if own_client:
            client.close()
