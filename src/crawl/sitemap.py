"""Fetch company slugs from the Sequoia sitemap."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

SITEMAP_URL = "https://sequoiacap.com/company-sitemap.xml"
COMPANY_URL_PREFIX = "https://sequoiacap.com/companies/"

USER_AGENT = "sequoia-oss-api/0.1 (+https://github.com/sequoia-oss-api)"


def fetch_company_slugs(client: httpx.Client | None = None) -> list[str]:
    """Return a list of company slugs from the sitemap."""
    own_client = client is None
    if own_client:
        client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
    try:
        resp = client.get(SITEMAP_URL)
        resp.raise_for_status()
        return _parse_slugs(resp.text)
    finally:
        if own_client:
            client.close()


def _parse_slugs(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    slugs: list[str] = []
    for url_el in root.findall("sm:url", ns):
        loc = url_el.findtext("sm:loc", default="", namespaces=ns)
        if loc.startswith(COMPANY_URL_PREFIX):
            slug = loc.removeprefix(COMPANY_URL_PREFIX).strip("/")
            if slug:
                slugs.append(slug)
    return slugs
