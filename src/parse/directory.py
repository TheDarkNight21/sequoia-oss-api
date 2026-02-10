"""Parse the Sequoia /our-companies/ directory listing for stage and partner data."""

from __future__ import annotations

import logging
import re
import time

import httpx
from bs4 import BeautifulSoup

from src.normalize.slugify import slugify
from src.normalize.stages import normalize_stage

logger = logging.getLogger(__name__)

DIRECTORY_URL = "https://sequoiacap.com/our-companies/"
USER_AGENT = "sequoia-oss-api/0.1 (+https://github.com/sequoia-oss-api)"


def fetch_directory_data(
    client: httpx.Client | None = None,
    delay: float = 1.0,
) -> dict[str, dict]:
    """Fetch all directory pages and return {slug: directory_data}.

    directory_data keys: sequoia_id, name, stage_raw, stage, partners_raw, first_partnered_raw
    """
    own_client = client is None
    if own_client:
        client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
            follow_redirects=True,
        )
    try:
        all_data: dict[str, dict] = {}
        page = 1
        while True:
            url = DIRECTORY_URL if page == 1 else f"{DIRECTORY_URL}?_paged={page}"
            logger.info("Fetching directory page %d: %s", page, url)
            resp = client.get(url)
            resp.raise_for_status()

            page_data = _parse_directory_page(resp.text)
            if not page_data:
                break

            all_data.update(page_data)
            logger.info("Page %d: %d companies (total so far: %d)", page, len(page_data), len(all_data))

            # Check if there are more pages
            total_pages = _extract_total_pages(resp.text)
            if page >= total_pages:
                break

            page += 1
            time.sleep(delay)

        logger.info("Directory fetch complete: %d companies", len(all_data))
        return all_data
    finally:
        if own_client:
            client.close()


def _parse_directory_page(html: str) -> dict[str, dict]:
    """Parse a single directory page's HTML table rows."""
    soup = BeautifulSoup(html, "lxml")
    fwp = soup.select_one(".facetwp-template")
    if not fwp:
        return {}

    results: dict[str, dict] = {}
    rows = [tr for tr in fwp.find_all("tr") if "child" not in (tr.get("class") or [])]

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 6:
            continue

        sequoia_id = cells[0].get_text(strip=True)
        name = cells[1].get_text(strip=True)
        stage_raw = cells[3].get_text(strip=True)
        partners_raw = cells[4].get_text(strip=True)
        first_partnered_raw = cells[5].get_text(strip=True)

        slug = _name_to_slug(name, row)

        results[slug] = {
            "sequoia_id": sequoia_id or None,
            "name": name,
            "stage_raw": stage_raw,
            "stage": normalize_stage(stage_raw),
            "partners_raw": partners_raw,
            "first_partnered_raw": first_partnered_raw,
        }

    return results


def _name_to_slug(name: str, row) -> str:
    """Derive the URL slug from the company name or row data."""
    # Try to find a link to the company profile
    link = row.find("a", href=re.compile(r"/companies/"))
    if link:
        href = link["href"]
        match = re.search(r"/companies/([^/]+)/?", href)
        if match:
            return match.group(1)

    # Try the collapse target which has the sequoia ID
    target = row.get("data-target", "")
    if target:
        # #company_listing-218 -> we'd need a separate lookup
        pass

    return slugify(name)


def _extract_total_pages(html: str) -> int:
    """Extract total pages from FacetWP pager settings in the page."""
    match = re.search(r'"total_pages"\s*:\s*(\d+)', html)
    return int(match.group(1)) if match else 1


def merge_directory_data(
    companies: list[dict],
    directory: dict[str, dict],
) -> list[dict]:
    """Merge directory-level data (stage, sequoia_id) into company records."""
    merged_count = 0
    for company in companies:
        slug = company["slug"]
        dir_data = directory.get(slug)
        if dir_data:
            merged_count += 1
            # Fill in stage if not already set or if directory has better data
            if dir_data.get("stage"):
                company["current_stage"] = dir_data["stage"]
            # Fill in sequoia_id
            if dir_data.get("sequoia_id"):
                company["sequoia_id"] = dir_data["sequoia_id"]

    logger.info("Merged directory data for %d/%d companies", merged_count, len(companies))
    return companies
