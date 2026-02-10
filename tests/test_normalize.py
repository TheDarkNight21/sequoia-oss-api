"""Tests for normalization utilities."""

import pytest

from src.normalize.slugify import slugify
from src.normalize.stages import STAGE_ENUM, normalize_stage
from src.normalize.categories import normalize_category_id
from src.normalize.partners import normalize_partner_id


class TestSlugify:
    def test_simple(self):
        assert slugify("Stripe") == "stripe"

    def test_spaces(self):
        assert slugify("Open AI") == "open-ai"

    def test_punctuation(self):
        assert slugify("DoorDash, Inc.") == "doordash-inc"

    def test_leading_number(self):
        assert slugify("23andMe") == "23andme"

    def test_multi_word(self):
        assert slugify("Palo Alto Networks") == "palo-alto-networks"

    def test_trim(self):
        assert slugify("  hello  ") == "hello"

    def test_consecutive_hyphens(self):
        assert slugify("a - - b") == "a-b"

    def test_unicode(self):
        assert slugify("café") == "cafe"

    def test_empty(self):
        assert slugify("") == ""


class TestNormalizeStage:
    def test_growth(self):
        assert normalize_stage("Growth") == "growth"

    def test_preseed(self):
        assert normalize_stage("Pre-Seed/Seed") == "pre-seed-seed"

    def test_ipo(self):
        assert normalize_stage("IPO") == "ipo"

    def test_acquired(self):
        assert normalize_stage("Acquired") == "acquired"

    def test_unknown_label(self):
        assert normalize_stage("Something New") == "unknown"

    def test_none(self):
        assert normalize_stage(None) is None

    def test_empty(self):
        assert normalize_stage("") is None

    def test_whitespace(self):
        assert normalize_stage("  growth  ") == "growth"

    def test_all_values_in_enum(self):
        for raw in ["Pre-Seed/Seed", "Early", "Growth", "IPO", "Acquired"]:
            result = normalize_stage(raw)
            assert result in STAGE_ENUM


class TestNormalizeCategoryId:
    def test_simple(self):
        assert normalize_category_id("Enterprise Software") == "enterprise-software"

    def test_single_word(self):
        assert normalize_category_id("FinTech") == "fintech"

    def test_ampersand(self):
        assert normalize_category_id("Data & Analytics") == "data-analytics"


class TestNormalizePartnerId:
    def test_full_name(self):
        assert normalize_partner_id("Alfred Lin") == "alfred-lin"

    def test_multi_part(self):
        assert normalize_partner_id("Roelof Botha") == "roelof-botha"
