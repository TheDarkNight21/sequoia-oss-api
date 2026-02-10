"""Generate static JSON output files for GitHub Pages."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0.0"


def build_all(
    companies: list[dict[str, Any]],
    output_dir: str,
) -> None:
    """Build all static JSON files from a list of company records."""
    _ensure_dirs(output_dir)

    # companies/all.json
    _write_json(os.path.join(output_dir, "companies", "all.json"), companies)

    # companies/{slug}.json
    for company in companies:
        path = os.path.join(output_dir, "companies", f"{company['slug']}.json")
        _write_json(path, company)

    # stages/{stageId}.json
    stages = _group_by_stage(companies)
    for stage_id, entries in stages.items():
        path = os.path.join(output_dir, "stages", f"{stage_id}.json")
        _write_json(path, {
            "id": stage_id,
            "label": stage_id.replace("-", " ").title(),
            "companies": entries,
        })

    # categories/{categoryId}.json
    categories = _group_by_category(companies)
    for cat_id, (label, entries) in categories.items():
        path = os.path.join(output_dir, "categories", f"{cat_id}.json")
        _write_json(path, {
            "id": cat_id,
            "label": label,
            "companies": entries,
        })

    # partners/{partnerId}.json
    partners = _group_by_partner(companies)
    for partner_id, (name, entries) in partners.items():
        path = os.path.join(output_dir, "partners", f"{partner_id}.json")
        _write_json(path, {
            "id": partner_id,
            "name": name,
            "companies": entries,
        })

    # first-partnered/{year}.json
    by_year = _group_by_year(companies)
    for year, entries in by_year.items():
        path = os.path.join(output_dir, "first-partnered", f"{year}.json")
        _write_json(path, {
            "year": year,
            "companies": entries,
        })

    # meta.json
    meta = _build_meta(companies, stages, categories)
    _write_json(os.path.join(output_dir, "meta.json"), meta)


def _ensure_dirs(output_dir: str) -> None:
    for subdir in ("companies", "stages", "categories", "partners", "first-partnered"):
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)


def _company_summary(company: dict[str, Any]) -> dict[str, str]:
    return {
        "id": company["id"],
        "name": company["name"],
        "slug": company["slug"],
    }


def _group_by_stage(
    companies: list[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for c in companies:
        stage = c.get("current_stage")
        if stage:
            groups[stage].append(_company_summary(c))
    return dict(groups)


def _group_by_category(
    companies: list[dict[str, Any]],
) -> dict[str, tuple[str, list[dict[str, str]]]]:
    """Returns {category_id: (label, [summaries])}."""
    groups: dict[str, tuple[str, list[dict[str, str]]]] = {}
    for c in companies:
        for cat_id in c.get("categories", []):
            if cat_id not in groups:
                # Recover label from id (best effort)
                groups[cat_id] = (cat_id.replace("-", " ").title(), [])
            groups[cat_id][1].append(_company_summary(c))
    return groups


def _group_by_partner(
    companies: list[dict[str, Any]],
) -> dict[str, tuple[str, list[dict[str, str]]]]:
    """Returns {partner_id: (name, [summaries])}."""
    groups: dict[str, tuple[str, list[dict[str, str]]]] = {}
    for c in companies:
        for pid in c.get("partners", []):
            if pid not in groups:
                groups[pid] = (pid.replace("-", " ").title(), [])
            groups[pid][1].append(_company_summary(c))
    return groups


def _group_by_year(
    companies: list[dict[str, Any]],
) -> dict[int, list[dict[str, str]]]:
    groups: dict[int, list[dict[str, str]]] = defaultdict(list)
    for c in companies:
        year = c.get("first_partnered_year")
        if year:
            groups[year].append(_company_summary(c))
    return dict(groups)


def _build_meta(
    companies: list[dict[str, Any]],
    stages: dict[str, list],
    categories: dict[str, tuple[str, list]],
) -> dict[str, Any]:
    return {
        "last_updated_iso": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "total_companies": len(companies),
        "counts_by_stage": {k: len(v) for k, v in stages.items()},
        "counts_by_category": {k: len(v[1]) for k, v in categories.items()},
        "source_entry_url": "https://sequoiacap.com/our-companies/",
    }


def _write_json(path: str, data: Any) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
