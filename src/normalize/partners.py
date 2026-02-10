"""Partner normalization: convert partner names to stable IDs."""

from __future__ import annotations

from src.normalize.slugify import slugify


def normalize_partner_id(raw_name: str) -> str:
    """Return a normalized partner ID from a raw name."""
    return slugify(raw_name)


def make_partner_index_entry(
    partner_id: str,
    name: str,
    companies: list[dict],
) -> dict:
    """Build a partner index entry for /partners/{partnerId}.json.

    Args:
        partner_id: Normalized partner slug.
        name: Original display name.
        companies: List of company summary dicts (id, name, slug).
    """
    return {
        "id": partner_id,
        "name": name,
        "companies": companies,
    }
