#!/usr/bin/env python3
"""Main entry point: crawl Sequoia directory, parse profiles, build static JSON."""

from __future__ import annotations

import argparse
import logging
import sys

from src.crawl.fetcher import ContentCache, fetch_pages, make_client
from src.crawl.sitemap import fetch_company_slugs
from src.parse.company import parse_company
from src.parse.directory import fetch_directory_data, merge_directory_data
from src.build.static import build_all
from src.validate.completeness import report_completeness
from src.validate.schema import validate_companies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 50
DEFAULT_OUTPUT = "docs"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Sequoia static API")
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT,
        help=f"Max companies to fetch (default: {DEFAULT_LIMIT}, 0 = all)",
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable content caching (re-fetch everything)",
    )
    parser.add_argument(
        "--skip-directory", action="store_true",
        help="Skip fetching directory data (stage/partner enrichment)",
    )
    args = parser.parse_args()

    # 1. Discover company slugs from sitemap
    logger.info("Fetching company slugs from sitemap...")
    slugs = fetch_company_slugs()
    logger.info("Found %d companies in sitemap", len(slugs))

    if args.limit > 0:
        slugs = slugs[: args.limit]
    logger.info("Processing %d companies", len(slugs))

    # 2. Fetch directory data for stage enrichment
    directory_data: dict = {}
    if not args.skip_directory:
        logger.info("Fetching directory data for stage enrichment...")
        client = make_client()
        try:
            directory_data = fetch_directory_data(client=client)
        finally:
            client.close()
        logger.info("Got directory data for %d companies", len(directory_data))

    # 3. Fetch company profile pages (with caching)
    cache = None if args.no_cache else ContentCache()
    logger.info("Fetching %d company profile pages...", len(slugs))

    client = make_client()
    try:
        pages = fetch_pages(slugs, client=client, cache=cache)
    finally:
        client.close()

    logger.info("Got %d pages total", len(pages))

    # 4. Parse each company profile
    companies = []
    for slug, html in pages.items():
        try:
            record = parse_company(slug, html)
            companies.append(record)
        except Exception:
            logger.exception("Failed to parse %s", slug)

    logger.info("Parsed %d company records", len(companies))

    # 5. Merge directory data (stage, sequoia_id)
    if directory_data:
        companies = merge_directory_data(companies, directory_data)

    # 6. Validate against schema
    errors = validate_companies(companies)
    if errors:
        logger.error("Schema validation failed — aborting build")
        sys.exit(1)

    # 7. Report extraction completeness
    report_completeness(companies)

    # 8. Build static JSON
    logger.info("Building static JSON output to %s/", args.output)
    build_all(companies, args.output)

    logger.info("Done. %d companies written to %s/", len(companies), args.output)


if __name__ == "__main__":
    main()
