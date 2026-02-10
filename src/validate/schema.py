"""Validate company records against the JSON Schema."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from jsonschema import Draft202012Validator

logger = logging.getLogger(__name__)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir, "schema", "company.schema.json",
)


def _load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_companies(companies: list[dict[str, Any]]) -> list[dict]:
    """Validate all company records against the schema.

    Returns a list of error dicts: [{"slug": str, "errors": [str]}].
    Companies that pass validation return no entries.
    """
    schema = _load_schema()
    validator = Draft202012Validator(schema)

    all_errors: list[dict] = []
    for company in companies:
        errors = sorted(validator.iter_errors(company), key=lambda e: list(e.path))
        if errors:
            slug = company.get("slug", "unknown")
            error_messages = [
                f"{'.'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
                for e in errors
            ]
            all_errors.append({"slug": slug, "errors": error_messages})

    if all_errors:
        total_errs = sum(len(e["errors"]) for e in all_errors)
        logger.warning(
            "Schema validation: %d errors across %d companies",
            total_errs, len(all_errors),
        )
        for entry in all_errors[:10]:  # Log first 10
            logger.warning("  %s:", entry["slug"])
            for msg in entry["errors"][:5]:
                logger.warning("    - %s", msg)
    else:
        logger.info("Schema validation: all %d companies passed", len(companies))

    return all_errors
