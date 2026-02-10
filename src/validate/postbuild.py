#!/usr/bin/env python3
"""Post-build validation for safe publishing.

Checks that a build directory contains valid, complete output before
it replaces the live docs/ directory. Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REQUIRED_SUBDIRS = ("companies", "stages", "categories", "partners", "first-partnered")
MIN_COMPANIES = 100  # Fail if fewer than this — guards against partial crawls


def validate_build(build_dir: str) -> list[str]:
    """Return a list of error strings. Empty list means the build is valid."""
    errors: list[str] = []

    # 1. Check meta.json exists and is valid
    meta_path = os.path.join(build_dir, "meta.json")
    if not os.path.isfile(meta_path):
        errors.append("meta.json not found")
        return errors  # Can't continue without meta

    try:
        with open(meta_path) as f:
            meta = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        errors.append(f"meta.json unreadable: {e}")
        return errors

    # 2. Check required meta fields
    for field in ("last_updated_iso", "schema_version", "total_companies"):
        if field not in meta:
            errors.append(f"meta.json missing field: {field}")

    # 3. Check company count above minimum
    total = meta.get("total_companies", 0)
    if total < MIN_COMPANIES:
        errors.append(
            f"total_companies={total} is below minimum threshold ({MIN_COMPANIES})"
        )

    # 4. Check required subdirectories exist and are non-empty
    for subdir in REQUIRED_SUBDIRS:
        subdir_path = os.path.join(build_dir, subdir)
        if not os.path.isdir(subdir_path):
            errors.append(f"Missing directory: {subdir}/")
            continue
        files = [f for f in os.listdir(subdir_path) if f.endswith(".json")]
        if not files:
            errors.append(f"Empty directory: {subdir}/")

    # 5. Check companies/all.json exists and is a non-empty array
    all_path = os.path.join(build_dir, "companies", "all.json")
    if os.path.isfile(all_path):
        try:
            with open(all_path) as f:
                all_data = json.load(f)
            if not isinstance(all_data, list) or len(all_data) < MIN_COMPANIES:
                errors.append(
                    f"companies/all.json has {len(all_data) if isinstance(all_data, list) else 0} "
                    f"entries, expected >= {MIN_COMPANIES}"
                )
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"companies/all.json unreadable: {e}")
    else:
        errors.append("companies/all.json not found")

    # 6. Spot-check: each company slug file from all.json should exist
    if os.path.isfile(all_path) and not errors:
        try:
            with open(all_path) as f:
                companies = json.load(f)
            missing = 0
            for c in companies:
                slug = c.get("slug", "")
                if not os.path.isfile(os.path.join(build_dir, "companies", f"{slug}.json")):
                    missing += 1
            if missing > 0:
                errors.append(f"{missing} company slug files missing from companies/")
        except Exception:
            pass  # Already caught above

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <build_dir>")
        sys.exit(1)

    build_dir = sys.argv[1]
    if not os.path.isdir(build_dir):
        logger.error("Build directory does not exist: %s", build_dir)
        sys.exit(1)

    errors = validate_build(build_dir)
    if errors:
        logger.error("Post-build validation FAILED (%d errors):", len(errors))
        for e in errors:
            logger.error("  - %s", e)
        sys.exit(1)
    else:
        logger.info("Post-build validation PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
