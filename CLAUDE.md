# CLAUDE.md
# Purpose: Make Claude Code an execution-only agent.
# Prompt creation happens in Codex CLI. Claude runs Codex, then executes the resulting plan.

## Operating Mode
You are an execution agent, not a planner.
- Do not rewrite requirements.
- Do not invent missing details.
- If required info is missing, ask ONE targeted question, then stop.
- Make the smallest change that achieves the objective.
- Prefer edits that are easy to review (small diffs, clear commits).
- Never broaden scope without explicit instruction.

## Primary Workflow
We use Codex CLI as the prompt and plan generator.

When the user wants work done, they will provide either:
1) A Codex instruction to generate a Work Packet, or
2) A Work Packet directly.

Your job:
- If a Work Packet is provided, execute it exactly.
- If a Work Packet is NOT provided, run Codex to produce one, then execute it.

## Codex Invocation Rules
If the user message contains one of these triggers, you MUST run Codex:
- `CODEX: ...`
- `MAKE_PACKET: ...`
- `PLAN_WITH_CODEX: ...`

### How to run Codex
Run this command in the repo root (adjust only if user specifies a different path):
- `codex`

Then paste the trigger content into Codex as the prompt.

### What to ask Codex for
In Codex, always request a "Work Packet" that is:
- explicit
- patch-driven where possible
- includes verification steps

Use this exact template in Codex:

Work Packet Template:
- Objective:
- Constraints:
- Repo Context Needed:
- Files in Scope:
- Commands to Run (exact):
- Edits to Make (unified diff or exact search/replace):
- Verification:
- Rollback Plan:
- Expected Output Format:

### Minimal Repo Context to feed Codex
Before opening Codex, gather only what is needed:
- list repo structure: `ls`
- identify relevant files: `find . -maxdepth 3 -type f | head -n 200` (or narrower)
- open relevant files: `sed -n '1,200p' path/to/file`
- read package scripts: `cat package.json` or `pyproject.toml` or `requirements.txt` if applicable
- identify test runner: `npm test`, `pytest`, etc.

Do NOT dump huge files into Codex.
Prefer:
- file paths
- short excerpts
- error messages
- relevant configs

If there is an error, always capture:
- command
- full stderr/stdout

## Execution Rules After Codex Returns a Work Packet
You MUST follow the Work Packet exactly.

### Allowed Actions
- Run terminal commands specified in the Work Packet
- Edit/create files in the repo as specified
- Run ONE additional diagnostic command if something fails (examples: `ls`, `pwd`, `git status`, `cat <file>`, `python -m pytest -q`)
Anything else requires asking permission.

### Disallowed Actions
- Refactoring not requested
- Dependency upgrades unless required for the fix
- Large formatting changes
- Renaming/restructuring without explicit instructions

## Output Format (Always)
Return results in this exact structure:

1) Summary
- What the Work Packet intended
- What you actually did

2) Changes
- Files changed (list)
- Key diffs or description (brief)

3) Commands Run
- Each command and the result (success/failure)

4) Verification
- Tests run, lint, build, manual checks
- Results and any failures

5) Follow-ups
- Only if required
- If blocked, ask ONE targeted question

## Error Handling
If a step fails:
- Stop immediately
- Report:
  - the failing command
  - the full error output
  - what you think caused it (1-2 sentences)
  - the smallest next fix to try
Then ask ONE targeted question if needed.

## Git Hygiene (if repo uses git)
- Check status before and after: `git status`
- Prefer small commits if user asked for commits.
- Do not push unless explicitly instructed.

## Examples

### Example 1: User wants Codex to generate a Work Packet
User: `MAKE_PACKET: Fix login error on OAuth callback and add a basic analytics page.`

You:
1. Collect minimal context (error logs, relevant files).
2. Run `codex`
3. Paste the request and context into Codex using the template.
4. When Codex outputs a Work Packet, execute it exactly.

### Example 2: User provides a Work Packet
User pastes a Work Packet.

You:
- Execute it exactly, no Codex needed unless the packet is ambiguous.

**Here is a phased development plan for this project:**

# Sequoia Static API (YC OSS style) – Claude Agent Plan (Path A)

## Goal
Build a static JSON “API” for Sequoia’s public portfolio directory, similar to yc-oss/api, served via GitHub Pages. Data source is Sequoia’s public directory and company profile pages only. Primary entry URL: https://sequoiacap.com/our-companies/

## Non goals
- No private or paid sources (Crunchbase, PitchBook, etc.).
- No live backend, no database required for serving.
- No claims of completeness beyond what Sequoia publicly lists.

## Compliance and Safety
- Check and comply with Sequoia robots and site terms before crawling.
- Use a clear User Agent string.
- Rate limit requests (start at 1 request per second).
- Avoid aggressive parallelization.
- Fail safely: do not publish partial builds.

---

## Phase 0 – Guardrails and Feasibility
### Tasks
1. Verify crawling is permitted by robots and terms for:
   - Directory page: https://sequoiacap.com/our-companies/
   - Company profile pages under https://sequoiacap.com/companies/
2. Define refresh cadence: daily.
3. Draft a Data Contract:
   - Source URLs
   - Field list (public only)
   - Update cadence
   - Attribution and disclaimers

### Deliverables
- docs/data-contract.md
- docs/field-list.md

---

## Phase 1 – Define API Contract and Normalization
### Endpoints (static files)
- /meta.json
- /companies/all.json
- /companies/{slug}.json
- /categories/{categoryId}.json
- /partners/{partnerId}.json
- /stages/{stageId}.json
- /first-partnered/{year}.json

### Canonical Company Schema (minimum viable)
- id: string (stable, e.g. "sequoia:{slug}")
- sequoia_id: string | null (if discoverable)
- name: string
- slug: string
- description: string | null
- website: string | null
- socials: object (keys: twitter, linkedin, etc.)
- categories: string[] (normalized ids)
- current_stage: string | null (enum)
- first_partnered_year: number | null
- partners: string[] (normalized partner ids)
- primary_partner: string | null
- milestones: object
  - founded_year: number | null
  - partnered_year: number | null
  - ipo_year: number | null
  - acquired_year: number | null
- team: object[]
  - name: string
  - role: string | null
- why_partnered: string | null
- source_urls: object
  - directory: string
  - profile: string

### Normalization Rules
- Slugify ids: lowercase, trim, replace spaces with hyphens, remove punctuation.
- Stage enum mapping: map Sequoia’s directory labels into a controlled set:
  - pre-seed-seed, early, growth, ipo, acquired, unknown
- Categories: normalize to ids, keep original label optionally.
- Partners: normalize names to ids, maintain a partner index.

### Deliverables
- schema/company.schema.json
- docs/endpoints.md
- src/normalize/*

---

## Phase 2 – Thin Vertical Slice (Proof of Concept)
### Tasks
1. Implement directory fetch and parse:
   - Pull first 50 companies from the directory listing.
   - Extract: name, profile URL, and any visible fields (stage, partner, first partnered, category) if present on listing.
2. Implement company profile parse:
   - Fetch each company page.
   - Parse: website, socials, categories, milestones, partner, team, why_partnered.
   - Prefer semantic anchors (section headings like “Milestones”, “Team”, “Partner”) over brittle CSS classes.
3. Generate static outputs for slice:
   - companies/all.json (50)
   - companies/{slug}.json per company
   - stages/{stageId}.json for at least one stage
4. Publish via GitHub Pages from docs/ or public/

### Deliverables
- Working GH Pages demo where JSON is accessible via browser/curl

---

## Phase 3 – Production Crawler and Parser
### Crawler Requirements
- Single entry discovery from directory page.
- Rate limit 1 rps with jitter.
- Retries with exponential backoff on 429 and transient 5xx.
- Local caching within run to avoid duplicate requests.

### Change Detection
- Store content hash per URL across runs.
- If unchanged, reuse prior parsed output.

### Parser Hardening
- Modular parsers:
  - src/parse/directory.ts
  - src/parse/company.ts
- Logging of extraction completeness per field:
  - e.g. percent of companies with primary_partner detected
- Snapshot tests for a small set of known pages to detect layout changes.

### Deliverables
- Test suite for parsing
- Run report summarizing extraction completeness

---

## Phase 4 – Full Dataset Build + Index Generation
### Tasks
1. Crawl all companies discovered from directory.
2. Parse every company profile page.
3. Validate every record against schema.
4. Build derived indexes:
   - categories/{categoryId}.json
   - partners/{partnerId}.json
   - stages/{stageId}.json
   - first-partnered/{year}.json
5. Generate top level lists:
   - companies/all.json
   - companies/{subset}.json if supported by public fields (e.g. ipo, acquired)

### Deliverables
- Full dataset published as static JSON
- Index endpoints populated and validated

---

## Phase 5 – Automation and Safe Publishing
### GitHub Actions
- Daily scheduled workflow + manual dispatch.
- Workflow steps:
  1. Install deps
  2. Run crawler and build into a temp build dir
  3. Validate JSON and counts
  4. Atomically replace published directory
  5. Commit outputs (or push to Pages branch)

### Safety
- Do not publish if validation fails.
- Keep last known good build.

### meta.json Requirements
- last_updated_iso
- schema_version
- total_companies
- counts_by_stage
- counts_by_category
- source_entry_url (directory page)

### Deliverables
- .github/workflows/refresh.yml
- docs/meta.json published

---

## Phase 6 – QA and Maintenance
### QA Rules
- Every company must have name, slug, profile URL.
- Stage must be enum or null with warning.
- Partners must resolve in partner index.

### Monitoring
- Detect layout breaks by:
  - sudden drop in extraction completeness
  - failed snapshot tests

### Versioning Policy
- Never remove fields without major schema bump.
- Add fields in backward compatible way when possible.

---

## Repo Structure (Recommended)
- src/
  - crawl/
  - parse/
  - normalize/
  - build/
  - validate/
- docs/ (published output for GH Pages)
  - meta.json
  - companies/
  - categories/
  - partners/
  - stages/
  - first-partnered/
- schema/
- .github/workflows/

---

## Definition of Done
- Daily GH Action produces updated JSON files and publishes to GH Pages.
- /companies/all.json + /companies/{slug}.json resolve correctly.
- Index endpoints (categories, partners, stages, first-partnered) are valid and consistent with canonical company records.
- meta.json reflects current counts and last update.
