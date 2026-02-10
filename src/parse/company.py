"""Parse a Sequoia company profile page into a canonical record."""

from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.normalize.categories import normalize_category_id
from src.normalize.partners import normalize_partner_id
from src.normalize.slugify import slugify
from src.normalize.stages import normalize_stage

DIRECTORY_BASE = "https://sequoiacap.com/our-companies/"
PROFILE_BASE = "https://sequoiacap.com/companies/"


def parse_company(slug: str, html: str) -> dict[str, Any]:
    """Parse a company profile HTML into a canonical company dict."""
    soup = BeautifulSoup(html, "lxml")

    name = _extract_name(soup, slug)
    description = _extract_description(soup)
    website = _extract_website(soup)
    socials = _extract_socials(soup)
    categories_raw = _extract_categories(soup)
    milestones = _extract_milestones(soup)
    team = _extract_team(soup)
    partners_raw = _extract_partners(soup)
    why_partnered = _extract_why_partnered(soup)

    # Derive stage from milestones
    current_stage = _infer_stage(milestones, soup)
    first_partnered_year = milestones.get("partnered_year")

    category_ids = [normalize_category_id(c) for c in categories_raw]
    partner_ids = [normalize_partner_id(p) for p in partners_raw]
    primary_partner = partner_ids[0] if partner_ids else None

    return {
        "id": f"sequoia:{slug}",
        "sequoia_id": None,
        "name": name,
        "slug": slug,
        "description": description,
        "website": website,
        "socials": socials,
        "categories": category_ids,
        "current_stage": current_stage,
        "first_partnered_year": first_partnered_year,
        "partners": partner_ids,
        "primary_partner": primary_partner,
        "milestones": milestones,
        "team": team,
        "why_partnered": why_partnered,
        "source_urls": {
            "directory": f"{DIRECTORY_BASE}",
            "profile": f"{PROFILE_BASE}{slug}/",
        },
    }


# --- Extractors ---


def _extract_name(soup: BeautifulSoup, slug: str) -> str:
    """Extract company name from the analytics track call or page title."""
    # Primary: analytics.track('Viewed Company', {"title": "Name", ...})
    for script in soup.find_all("script"):
        text = script.string or ""
        match = re.search(
            r"""analytics\.track\(\s*['"]Viewed Company['"]\s*,\s*(\{.*?\})""",
            text,
            re.DOTALL,
        )
        if match:
            try:
                data = json.loads(match.group(1))
                if data.get("title"):
                    return data["title"]
            except (json.JSONDecodeError, KeyError):
                pass

    # Fallback: first img alt in the header area
    img = soup.select_one("img[alt]")
    if img and img.get("alt"):
        return img["alt"]

    # Last resort: title tag
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        return title_tag.string.split("|")[0].strip()

    return slug.replace("-", " ").title()


def _extract_description(soup: BeautifulSoup) -> str | None:
    """Extract company description from the profile page."""
    # Primary: the wysiwyg block that holds the company description
    wysiwyg = soup.select_one("div.wysiwyg.wysiwyg--fs-lg")
    if wysiwyg:
        p = wysiwyg.find("p")
        if p:
            text = p.get_text(strip=True)
            if text:
                return text

    # Fallback: meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()

    # OG description
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content"):
        return og["content"].strip()

    return None


def _extract_website(soup: BeautifulSoup) -> str | None:
    """Extract the company website URL."""
    # Look for links that aren't sequoiacap.com, twitter, linkedin, instagram, etc.
    social_domains = {
        "twitter.com", "linkedin.com", "instagram.com", "facebook.com",
        "sequoiacap.com", "youtube.com", "github.com",
    }
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        # The website link typically shows as "domain.com" text
        if (
            href.startswith("http")
            and not any(d in href for d in social_domains)
            and text
            and "." in text
            and len(text) < 60
            and "sequoia" not in text.lower()
            and "View" not in text
        ):
            return href
    return None


def _extract_socials(soup: BeautifulSoup) -> dict[str, str]:
    """Extract social media links."""
    socials: dict[str, str] = {}
    platform_patterns = {
        "twitter": "twitter.com",
        "linkedin": "linkedin.com",
        "instagram": "instagram.com",
        "facebook": "facebook.com",
        "youtube": "youtube.com",
        "github": "github.com",
    }
    for a in soup.find_all("a", href=True):
        href = a["href"]
        for platform, domain in platform_patterns.items():
            if domain in href and platform not in socials:
                socials[platform] = href
                break
    return socials


def _extract_categories(soup: BeautifulSoup) -> list[str]:
    """Extract category labels from category filter links."""
    cats: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "_categories=" in href:
            label = a.get_text(strip=True)
            if label and label not in cats:
                cats.append(label)
    return cats


def _find_section(soup: BeautifulSoup, heading_text: str) -> Tag | None:
    """Find the container following a heading with the given text."""
    for heading in soup.find_all(re.compile(r"^h[2-4]$")):
        if heading.get_text(strip=True).lower() == heading_text.lower():
            return heading
    return None


def _extract_milestones(soup: BeautifulSoup) -> dict[str, int | None]:
    """Extract milestone years from the Milestones section."""
    milestones: dict[str, int | None] = {
        "founded_year": None,
        "partnered_year": None,
        "ipo_year": None,
        "acquired_year": None,
    }
    heading = _find_section(soup, "Milestones")
    if not heading:
        return milestones

    # Look at the list items following the heading
    container = heading.find_next(["ul", "ol", "div"])
    if not container:
        return milestones

    text_items: list[str] = []
    if container.name in ("ul", "ol"):
        text_items = [li.get_text(strip=True) for li in container.find_all("li")]
    else:
        text_items = [container.get_text(strip=True)]

    for text in text_items:
        year_match = re.search(r"(\d{4})", text)
        if not year_match:
            continue
        year = int(year_match.group(1))
        lower = text.lower()
        if "founded" in lower:
            milestones["founded_year"] = year
        elif "partnered" in lower:
            milestones["partnered_year"] = year
        elif "ipo" in lower:
            milestones["ipo_year"] = year
        elif "acquired" in lower or "acquisition" in lower:
            milestones["acquired_year"] = year

    return milestones


def _extract_team(soup: BeautifulSoup) -> list[dict[str, str | None]]:
    """Extract team members from the Team section."""
    heading = _find_section(soup, "Team")
    if not heading:
        return []

    container = heading.find_next(["ul", "ol"])
    if not container:
        return []

    team: list[dict[str, str | None]] = []
    for li in container.find_all("li"):
        name = li.get_text(strip=True)
        if name:
            team.append({"name": name, "role": None})
    return team


def _extract_partners(soup: BeautifulSoup) -> list[str]:
    """Extract partner names from the Partner(s) section."""
    # Try both singular and plural headings
    heading = _find_section(soup, "Partners") or _find_section(soup, "Partner")
    if not heading:
        return []

    container = heading.find_next(["ul", "ol"])
    if not container:
        return []

    return [li.get_text(strip=True) for li in container.find_all("li") if li.get_text(strip=True)]


def _extract_why_partnered(soup: BeautifulSoup) -> str | None:
    """Extract the 'Why We Partnered' text if present."""
    for heading_text in ("Why We Partnered", "Why Sequoia Partnered"):
        heading = _find_section(soup, heading_text)
        if heading:
            p = heading.find_next("p")
            if p:
                return p.get_text(strip=True)
    return None


def _infer_stage(milestones: dict[str, int | None], soup: BeautifulSoup) -> str | None:
    """Infer current stage from milestones."""
    if milestones.get("acquired_year"):
        return "acquired"
    if milestones.get("ipo_year"):
        return "ipo"
    # Cannot reliably determine pre-seed-seed/early/growth from profile page alone
    return None
