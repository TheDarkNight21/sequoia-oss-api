"""Stage normalization: map raw directory labels to a controlled enum."""

from __future__ import annotations

STAGE_ENUM = frozenset({
    "pre-seed-seed",
    "early",
    "growth",
    "ipo",
    "acquired",
    "unknown",
})

# Mapping from known raw labels (lowercased) to canonical stage IDs.
# Extend this as new labels are discovered on the Sequoia directory.
_RAW_TO_STAGE: dict[str, str] = {
    "pre-seed/seed": "pre-seed-seed",
    "pre-seed": "pre-seed-seed",
    "seed": "pre-seed-seed",
    "early": "early",
    "early stage": "early",
    "growth": "growth",
    "growth stage": "growth",
    "ipo": "ipo",
    "public": "ipo",
    "acquired": "acquired",
    "acquisition": "acquired",
}


def normalize_stage(raw: str | None) -> str | None:
    """Return the canonical stage ID for a raw label, or None if empty.

    Falls back to 'unknown' for non-empty labels that don't match any known mapping.
    """
    if raw is None:
        return None
    cleaned = raw.strip().lower()
    if not cleaned:
        return None
    return _RAW_TO_STAGE.get(cleaned, "unknown")
