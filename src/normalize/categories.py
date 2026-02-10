"""Category normalization: convert raw category labels to stable IDs."""

from __future__ import annotations

from src.normalize.slugify import slugify


def normalize_category_id(raw_label: str) -> str:
    """Return a normalized category ID from a raw label."""
    return slugify(raw_label)


def make_category_index_entry(
    category_id: str,
    label: str,
    companies: list[dict],
) -> dict:
    """Build a category index entry for /categories/{categoryId}.json.

    Args:
        category_id: Normalized category slug.
        label: Original display label.
        companies: List of company summary dicts (id, name, slug).
    """
    return {
        "id": category_id,
        "label": label,
        "companies": companies,
    }
