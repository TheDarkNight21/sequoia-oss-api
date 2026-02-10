# Sequoia OSS API

Static JSON API for the Sequoia Capital portfolio directory. Data is sourced by crawling the public company directory at `https://sequoiacap.com/our-companies/` and the individual company profile pages (`https://sequoiacap.com/companies/{slug}/`). The build outputs live in `docs/` for GitHub Pages hosting.

## Metadata

Current dataset metadata (from `docs/meta.json`):

- API endpoint: `https://thedarknight21.github.io/sequoia-oss-api/meta.json`
- Last updated (ISO): `2026-02-10T20:27:09.156958+00:00`
- Schema version: `1.0.0`
- Total companies: `393`
- Counts by stage:
  - acquired: `33`
  - growth: `157`
  - ipo: `66`
  - early: `77`
  - pre-seed-seed: `48`
- Counts by category:
  - gtm: `30`
  - infrastructure: `22`
  - consumer: `86`
  - hardware: `33`
  - healthcare: `34`
  - fintech: `40`
  - marketplace: `16`
  - data-analytics: `30`
  - developer-tools: `34`
  - security: `34`
  - operations: `32`
  - crypto: `22`
  - ai: `110`
  - productivity: `25`
  - legal: `9`
  - climate: `6`
  - defense: `4`

## APIs

All endpoints serve static JSON files via GitHub Pages.

Base URL: `https://thedarknight21.github.io/sequoia-oss-api/`

- `GET /meta.json`
- `GET /companies/all.json`
- `GET /companies/{slug}.json`
- `GET /categories/{categoryId}.json`
- `GET /partners/{partnerId}.json`
- `GET /stages/{stageId}.json` (pre-seed-seed, early, growth, ipo, acquired, unknown)
- `GET /first-partnered/{year}.json`

## Schema

Company records follow `schema/company.schema.json`.

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Stable identifier in the form `sequoia:{slug}`. |
| `sequoia_id` | string or null | Sequoia's internal identifier if discoverable from the site. |
| `name` | string | Company display name. |
| `slug` | string | URL-safe slug derived from the company name. |
| `description` | string or null | Short company description from the profile page. |
| `website` | string (uri) or null | Company website URL. |
| `socials` | object | Social media links keyed by platform name. |
| `socials.<platform>` | string (uri) | Social media URL for a platform key. |
| `categories` | array of string | Normalized category IDs assigned to this company. |
| `current_stage` | string or null | Current investment stage: pre-seed-seed, early, growth, ipo, acquired, unknown. |
| `first_partnered_year` | integer or null | Year Sequoia first partnered with this company. |
| `partners` | array of string | Normalized partner IDs associated with this company. |
| `primary_partner` | string or null | Normalized ID of the primary Sequoia partner. |
| `milestones` | object | Key milestone years for the company. |
| `milestones.founded_year` | integer or null | Company founded year. |
| `milestones.partnered_year` | integer or null | Year Sequoia partnered. |
| `milestones.ipo_year` | integer or null | IPO year. |
| `milestones.acquired_year` | integer or null | Acquisition year. |
| `team` | array of object | Key team members listed on the company profile. |
| `team[].name` | string | Team member name. |
| `team[].role` | string or null | Team member role/title. |
| `why_partnered` | string or null | Sequoia's stated reason for partnering, if available. |
| `source_urls` | object | URLs from which this record was sourced. |
| `source_urls.directory` | string (uri) | URL of the company's entry in the directory listing. |
| `source_urls.profile` | string (uri) | URL of the company's dedicated profile page. |

## Usage

### Via HTTP (no clone needed)

The API is live at `https://thedarknight21.github.io/sequoia-oss-api/`. Fetch any endpoint directly:

```bash
# Get all companies
curl https://thedarknight21.github.io/sequoia-oss-api/companies/all.json

# Get a single company
curl https://thedarknight21.github.io/sequoia-oss-api/companies/airbnb.json

# Get metadata
curl https://thedarknight21.github.io/sequoia-oss-api/meta.json

# Filter by category, stage, partner, or year
curl https://thedarknight21.github.io/sequoia-oss-api/categories/ai.json
curl https://thedarknight21.github.io/sequoia-oss-api/stages/ipo.json
curl https://thedarknight21.github.io/sequoia-oss-api/partners/alfred-lin.json
curl https://thedarknight21.github.io/sequoia-oss-api/first-partnered/2020.json
```

### Local (clone the repo)

```bash
git clone https://github.com/TheDarkNight21/sequoia-oss-api.git
cd sequoia-oss-api
```

All data is in `docs/` — no build step needed:

```bash
# Read locally with jq
cat docs/companies/all.json | jq '.[0]'
cat docs/companies/stripe.json | jq '.name, .website, .categories'

# Use in Python
python -c "import json; data = json.load(open('docs/companies/all.json')); print(len(data), 'companies')"
```

To rebuild the dataset from scratch:

```bash
pip install -r requirements.txt
python run_build.py --limit 0 --output docs
```

## How It Works

- Crawler fetches the Sequoia directory and per-company profile pages.
- A static build compiles normalized JSON to `docs/`.
- GitHub Pages serves the `docs/` output as a static API.
- A daily GitHub Actions workflow refreshes the data automatically.

## License / Attribution

This project aggregates publicly available information from Sequoia Capital's company directory. Source: `https://sequoiacap.com/our-companies/`.
