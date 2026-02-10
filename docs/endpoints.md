# API Endpoints

All endpoints serve static JSON files via GitHub Pages.

Base URL: `https://<owner>.github.io/sequoia-oss-api/`

---

## GET /meta.json

Build metadata and dataset summary.

**Response**

```json
{
  "last_updated_iso": "2026-02-10T00:00:00Z",
  "schema_version": "1.0.0",
  "total_companies": 350,
  "counts_by_stage": {
    "pre-seed-seed": 40,
    "early": 80,
    "growth": 120,
    "ipo": 60,
    "acquired": 30,
    "unknown": 20
  },
  "counts_by_category": {
    "enterprise": 90,
    "consumer": 70,
    "fintech": 50
  },
  "source_entry_url": "https://sequoiacap.com/our-companies/"
}
```

---

## GET /companies/all.json

Array of all company records. Each element follows the [company schema](../schema/company.schema.json).

**Response** — array of company objects.

```json
[
  {
    "id": "sequoia:example-co",
    "name": "Example Co",
    "slug": "example-co",
    "...": "..."
  }
]
```

---

## GET /companies/{slug}.json

Single company record by slug.

**Path parameters**

| Param | Type   | Description                  |
|-------|--------|------------------------------|
| slug  | string | URL-safe company identifier  |

**Response** — single company object per the schema.

---

## GET /categories/{categoryId}.json

List of company summaries (id, name, slug) belonging to a category.

**Path parameters**

| Param      | Type   | Description               |
|------------|--------|---------------------------|
| categoryId | string | Normalized category slug  |

**Response**

```json
{
  "id": "enterprise",
  "label": "Enterprise",
  "companies": [
    { "id": "sequoia:example-co", "name": "Example Co", "slug": "example-co" }
  ]
}
```

---

## GET /partners/{partnerId}.json

List of company summaries associated with a Sequoia partner.

**Path parameters**

| Param     | Type   | Description              |
|-----------|--------|--------------------------|
| partnerId | string | Normalized partner slug  |

**Response**

```json
{
  "id": "jane-doe",
  "name": "Jane Doe",
  "companies": [
    { "id": "sequoia:example-co", "name": "Example Co", "slug": "example-co" }
  ]
}
```

---

## GET /stages/{stageId}.json

List of company summaries at a given investment stage.

**Path parameters**

| Param   | Type   | Description                                                         |
|---------|--------|---------------------------------------------------------------------|
| stageId | string | One of: pre-seed-seed, early, growth, ipo, acquired, unknown        |

**Response**

```json
{
  "id": "growth",
  "label": "Growth",
  "companies": [
    { "id": "sequoia:example-co", "name": "Example Co", "slug": "example-co" }
  ]
}
```

---

## GET /first-partnered/{year}.json

List of company summaries first partnered in a given year.

**Path parameters**

| Param | Type    | Description  |
|-------|---------|--------------|
| year  | integer | Four-digit year (e.g. 2023) |

**Response**

```json
{
  "year": 2023,
  "companies": [
    { "id": "sequoia:example-co", "name": "Example Co", "slug": "example-co" }
  ]
}
```
