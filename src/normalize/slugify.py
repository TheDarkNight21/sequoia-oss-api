"""Slugify utility for generating stable, URL-safe identifiers."""

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert text to a lowercase, hyphen-separated slug.

    Rules (from Phase 1 spec):
    - Lowercase
    - Trim whitespace
    - Replace spaces with hyphens
    - Remove punctuation (keep alphanumeric and hyphens)
    - Collapse consecutive hyphens
    - Strip leading/trailing hyphens
    """
    text = text.strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text
