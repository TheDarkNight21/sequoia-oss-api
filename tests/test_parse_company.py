"""Snapshot tests for company profile parser.

These tests parse saved HTML snapshots and assert expected field values.
If a test fails after a site layout change, inspect the diff and update
the snapshot or parser accordingly.
"""

import os

import pytest

from src.parse.company import parse_company

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")


def _load_snapshot(slug: str) -> str:
    path = os.path.join(SNAPSHOT_DIR, f"{slug}.html")
    with open(path) as f:
        return f.read()


class TestStripe:
    @pytest.fixture(autouse=True)
    def parse(self):
        self.record = parse_company("stripe", _load_snapshot("stripe"))

    def test_name(self):
        assert self.record["name"] == "Stripe"

    def test_id(self):
        assert self.record["id"] == "sequoia:stripe"

    def test_slug(self):
        assert self.record["slug"] == "stripe"

    def test_website(self):
        assert self.record["website"] == "https://stripe.com"

    def test_description(self):
        assert self.record["description"] is not None
        assert "Stripe" in self.record["description"]

    def test_categories(self):
        assert "fintech" in self.record["categories"]

    def test_milestones_founded(self):
        assert self.record["milestones"]["founded_year"] == 2010

    def test_milestones_partnered(self):
        assert self.record["milestones"]["partnered_year"] == 2010

    def test_team(self):
        names = [t["name"] for t in self.record["team"]]
        assert "John Collison" in names
        assert "Patrick Collison" in names

    def test_partners(self):
        assert "michael-moritz" in self.record["partners"]

    def test_socials(self):
        assert "twitter" in self.record["socials"]
        assert "linkedin" in self.record["socials"]

    def test_source_urls(self):
        assert self.record["source_urls"]["profile"] == "https://sequoiacap.com/companies/stripe/"


class TestAirbnb:
    @pytest.fixture(autouse=True)
    def parse(self):
        self.record = parse_company("airbnb", _load_snapshot("airbnb"))

    def test_name(self):
        assert self.record["name"] == "Airbnb"

    def test_website(self):
        assert "airbnb.com" in self.record["website"]

    def test_categories(self):
        assert "consumer" in self.record["categories"]
        assert "marketplace" in self.record["categories"]

    def test_milestones_ipo(self):
        assert self.record["milestones"]["ipo_year"] == 2020

    def test_stage_inferred(self):
        # IPO milestone should infer stage as "ipo"
        assert self.record["current_stage"] == "ipo"

    def test_milestones_founded(self):
        assert self.record["milestones"]["founded_year"] == 2007

    def test_milestones_partnered(self):
        assert self.record["milestones"]["partnered_year"] == 2009

    def test_team(self):
        names = [t["name"] for t in self.record["team"]]
        assert "Brian Chesky" in names

    def test_partners(self):
        assert "alfred-lin" in self.record["partners"]

    def test_socials_instagram(self):
        assert "instagram" in self.record["socials"]


class TestDoorDash:
    @pytest.fixture(autouse=True)
    def parse(self):
        self.record = parse_company("doordash", _load_snapshot("doordash"))

    def test_name(self):
        assert self.record["name"] == "DoorDash"

    def test_website(self):
        assert "doordash.com" in self.record["website"]

    def test_milestones_ipo(self):
        assert self.record["milestones"]["ipo_year"] == 2020

    def test_stage_inferred(self):
        assert self.record["current_stage"] == "ipo"

    def test_milestones_founded(self):
        assert self.record["milestones"]["founded_year"] == 2013

    def test_first_partnered_year(self):
        assert self.record["first_partnered_year"] == 2014

    def test_team(self):
        names = [t["name"] for t in self.record["team"]]
        assert "Tony Xu" in names

    def test_partners(self):
        assert "alfred-lin" in self.record["partners"]
