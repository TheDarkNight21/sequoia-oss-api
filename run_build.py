#!/usr/bin/env python3
"""Main entry point: crawl Sequoia directory, parse profiles, build static JSON."""

from __future__ import annotations

import argparse
import logging
import sys

from src.crawl.fetcher import fetch_pages, make_client
from src.crawl.sitemap import fetch_company_slugs
from src.parse.company import parse_company
from src.build.static import build_all

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
        help=f"Max companies to fetch (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    logger.info("Fetching company slugs from sitemap...")
    slugs = fetch_company_slugs()
    logger.info("Found %d companies in sitemap", len(slugs))

    slugs = slugs[: args.limit]
    logger.info("Fetching %d company profile pages...", len(slugs))

    client = make_client()
    try:
        pages = fetch_pages(slugs, client=client)
    finally:
        client.close()

    logger.info("Fetched %d pages successfully", len(pages))

    companies = []
    for slug, html in pages.items():
        try:
            record = parse_company(slug, html)
            companies.append(record)
        except Exception:
            logger.exception("Failed to parse %s", slug)

    logger.info("Parsed %d company records", len(companies))

    logger.info("Building static JSON output to %s/", args.output)
    build_all(companies, args.output)

    logger.info("Done. %d companies written to %s/", len(companies), args.output)


if __name__ == "__main__":
    main()
