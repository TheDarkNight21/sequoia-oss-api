"""Report extraction completeness per field across all company records."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Fields to check and how to determine if they're "present"
_SCALAR_FIELDS = [
    "description",
    "website",
    "current_stage",
    "first_partnered_year",
    "primary_partner",
    "why_partnered",
    "sequoia_id",
]

_LIST_FIELDS = [
    "categories",
    "partners",
    "team",
]

_MILESTONE_FIELDS = [
    "milestones.founded_year",
    "milestones.partnered_year",
    "milestones.ipo_year",
    "milestones.acquired_year",
]


def report_completeness(companies: list[dict[str, Any]]) -> dict[str, dict]:
    """Log and return field completeness stats.

    Returns {field_name: {"count": int, "total": int, "pct": float}}.
    """
    total = len(companies)
    if total == 0:
        logger.warning("No companies to report on")
        return {}

    stats: dict[str, dict] = {}

    for field in _SCALAR_FIELDS:
        count = sum(1 for c in companies if c.get(field) is not None)
        stats[field] = {"count": count, "total": total, "pct": round(count / total * 100, 1)}

    for field in _LIST_FIELDS:
        count = sum(1 for c in companies if c.get(field))
        stats[field] = {"count": count, "total": total, "pct": round(count / total * 100, 1)}

    for dotted in _MILESTONE_FIELDS:
        _, sub_field = dotted.split(".")
        count = sum(
            1 for c in companies
            if c.get("milestones", {}).get(sub_field) is not None
        )
        stats[dotted] = {"count": count, "total": total, "pct": round(count / total * 100, 1)}

    # Social platforms
    all_platforms: set[str] = set()
    for c in companies:
        all_platforms.update(c.get("socials", {}).keys())
    for platform in sorted(all_platforms):
        count = sum(1 for c in companies if platform in c.get("socials", {}))
        stats[f"socials.{platform}"] = {"count": count, "total": total, "pct": round(count / total * 100, 1)}

    # Log the report
    logger.info("=== Extraction Completeness Report ===")
    logger.info("Total companies: %d", total)
    for field, s in stats.items():
        bar = "#" * int(s["pct"] / 5) + "." * (20 - int(s["pct"] / 5))
        logger.info("  %-30s %3d/%3d (%5.1f%%) [%s]", field, s["count"], s["total"], s["pct"], bar)
    logger.info("=== End Report ===")

    return stats
