# TxAlert — Active Codex Prompts And Team Plan

This file replaces the older scattered B/F/A prompt list. Use it as the source of truth for the hackathon build.

## Important Corrections

- `AGENTS.md` now exists. Future prompts should say: **Read `AGENTS.md` and `CODEX_PROMPTS.md` first.**
- The newest architecture adds entity resolution, risk scoring, and pattern detection. For a 3-person hackathon team, build these as pragmatic demo-ready modules first, not a full research-grade ML platform.
- `README.md` currently overstates some implementation status. The status table below is the accurate code status.
- Keep the safer B3 framing: this helps legal aid organizations check public records the way a paralegal would, with bounded queries and respectful sleeps.
- Shift Miro ownership to Member 2 because that person owns frontend + visualization, even though `miro_service.py` lives in `backend/services/`.

## Team Split

| Member | Role | Owns |
|---|---|---|
| Bigyan | Backend + Agents + Data | Backend scaffold, Supabase, court scraper, monitor, FastAPI routes, alert orchestration, MCP, lightweight entity resolution integration |
| Member 2 | Frontend + Miro | Next.js app, dashboard UX, case cards, answer modal, API client/store, Miro visual board service |
| Member 3 | Algorithms + Risk | Deadline, limitations, collector scoring, property lookup, feature engineering, risk scoring, pattern detection tests |

## Current Implementation Status

| Area | Status | Notes |
|---|---|---|
| `backend/models/case.py` | Done baseline | Needs extension fields for entity/risk/pattern data |
| `backend/services/court_scraper.py` | Partial | Harris async scraper implemented defensively; live endpoint/payload unverified; Travis not built |
| `backend/agents/court_monitor.py` | Partial | Bounded Supabase monitor implemented; does not yet call limitations/scorer/risk/patterns |
| `backend/services/deadline_calculator.py` | Partial | Function exists, but A1 dataclass contract and tests are not done |
| `backend/services/limitations_checker.py` | Not started | Placeholder only |
| `backend/services/collector_scorer.py` | Not started | Placeholder only |
| `backend/services/property_lookup.py` | Not started | Placeholder only |
| `backend/agents/case_analyzer.py` | Not started | Placeholder only |
| `backend/agents/alert_generator.py` | Not started | Placeholder only |
| `backend/services/miro_service.py` | Not started | Placeholder only |
| `backend/main.py` | Not started | Placeholder only; README saying done is inaccurate |
| `backend/mcp/server.py` | Not started | Placeholder only |
| `frontend/` | Not started | No Next.js app yet |
| `layer1_entity/` | Not started | Needed only for enhanced entity/risk story |
| `layer2_risk/` | Not started | Build heuristic/demo model first |
| `layer3_patterns/` | Not started | Build simple pattern detector first |

## Bigyan — Backend + Agents

### B0 — Sync And Read Context

```text
Read AGENTS.md, CODEX_PROMPTS.md, README.md, TEAM_ARCHITECTURE.md, MODULE_OWNERSHIP.md, and SETUP.md.
Check git status. Do not overwrite other teammates' changes.
Report which backend steps are done, partial, or missing before editing.
```

### B1 — Backend Scaffold

Status: done.

Only revisit if models need extension fields from Member 3.

### B2 — Court Scraper Verification + Travis Fallback

Status: partial.

```text
In backend/services/court_scraper.py, verify the existing Harris County public API integration.

Keep:
- async search_cases_by_name(name: str, county: str = "harris") -> list[dict]
- async search_cases_by_address(address: str, county: str = "harris") -> list[dict]
- max 3 retries with exponential backoff
- empty list on any error

Add:
- county routing for "harris" and "travis"
- clear source attribution fields when possible: source_name, source_url
- a small parser test using mocked JSON, not live scraping

Do not scrape behind login. If live endpoint shape is unknown, preserve defensive parsing and document what still needs manual portal verification.
```

### B3 — Monitoring Agent Loop

Status: partial.

```text
Update backend/agents/court_monitor.py.

run_monitor_cycle() should:
1. Load active WatchEntry records from Supabase using supabase_client
2. Process max 10 watch entries per cycle
3. Sleep 2 seconds between each county query
4. Call court_scraper.search_cases_by_name() or search_cases_by_address()
5. Skip duplicate case_number records in Supabase
6. For new cases, calculate deadline using deadline_calculator.calculate_deadline()
7. If available, enrich with limitations_checker, collector_scorer, risk_model, and pattern_detector
8. Save new CourtCase records to Supabase
9. Return list[CourtCase]

Wrap each watch entry in try/except. Log cycle start/end with timestamps. This is public-record checking for legal aid organizations, not private surveillance.
```

### B4 — Case Analyzer + Alert Orchestration

```text
In backend/agents/case_analyzer.py write analyze_case(case: CourtCase) -> dict.

Use deterministic fields first:
- deadline_date, days_remaining
- is_time_barred
- collector_win_rate
- default_risk_score
- pattern_description

Then optionally call OpenAI gpt-4.1 for a short JSON-only summary:
{
  "defenses": [],
  "strongest_defense": str,
  "urgency_note": str,
  "plain_language_summary": str
}

System prompt:
"You are a Texas legal aid information assistant. Analyze this public court record for practical legal information. Do not provide legal advice. Focus on statute of limitations, service issues, debt ownership proof, amount disputes, and bankruptcy discharge. Return JSON only."
```

### B5 — FastAPI Routes

```text
In backend/main.py create a FastAPI app.

Routes:
- POST /watch
- GET /alerts/{email}
- POST /check-now/{watch_id}
- DELETE /watch/{watch_id}
- GET /health

Load .env with python-dotenv. Add CORS for http://localhost:3000.
Use Supabase tables: watch_entries, court_cases, alerts.
After POST /watch, run an immediate check for that watch entry only.
Return stable JSON suitable for the frontend.
```

### B6 — Background Task

```text
In backend/main.py add a startup background task.

Every 24 hours:
1. run_monitor_cycle()
2. for each new case call case_analyzer.analyze_case()
3. call alert_generator.generate_alert()
4. save Alert to Supabase
5. call miro_service.create_case_board()
6. log email output for hackathon if SMTP is not configured

Use asyncio.create_task() and asyncio.sleep(86400).
```

### B7 — MCP Server

```text
In backend/mcp/server.py create a FastMCP server on port 8001 with 6 tools:
- watch_name
- watch_address
- get_active_alerts
- get_case_deadline
- check_statute_limits
- find_legal_aid

Each tool must have clear docstrings and call real backend services when available.
Keep all queries bounded and safe for public data.
```

### B8 — Entity Resolution Integration

```text
Create backend/layer1_entity/entity_resolver.py.

Implement async resolve_entity(plaintiff_name: str, case_type: str = "") -> dict.

For hackathon demo:
- use a curated dictionary of known debt collector aliases
- add fuzzy matching with difflib or rapidfuzz if installed
- return canonical_name, entity_id, confidence_score, subsidiaries, parent_company
- never crash; unknown plaintiffs return confidence 0 and canonical_name=plaintiff_name

Integrate this into court_monitor for new cases before risk scoring.
```

## Member 2 — Frontend + Miro

### F1 — Next.js Scaffold

```text
Read AGENTS.md and CODEX_PROMPTS.md.
Create a Next.js 14 app in frontend/ with TypeScript and Tailwind.
Install zustand, immer, lucide-react, react-hot-toast.

Create:
- frontend/src/components/WatchForm.tsx
- frontend/src/components/AlertDashboard.tsx
- frontend/src/components/CaseCard.tsx
- frontend/src/components/AnswerModal.tsx
- frontend/src/components/RiskScoreCard.tsx
- frontend/src/components/PatternAlert.tsx
- frontend/src/lib/api.ts
- frontend/src/store/alertStore.ts
- frontend/src/app/page.tsx
```

### F2 — API Client + Store

```text
In frontend/src/lib/api.ts create typed fetch functions:
- createWatch(type, value, county, email)
- getAlerts(email)
- checkNow(watch_id)
- deleteWatch(watch_id)

In frontend/src/store/alertStore.ts create Zustand store:
- email, watches, alerts, loading, lastChecked
- setEmail, addWatch, removeWatch, fetchAlerts, checkNow

Use toast success/error. Poll alerts every 60 seconds when email is set.
```

### F3 — Watch Setup Form

```text
Build WatchForm with two tabs:
- Watch My Name
- Watch My Address

Fields:
- full name or street address
- county dropdown: Harris, Travis, Dallas, Bexar
- email

Design:
- dark background #0F0F0F
- urgent red #FF4444
- Geist Mono for inputs
- mobile responsive
- plain language, trustworthy, no legal jargon
```

### F4 — Alert Dashboard

```text
Build AlertDashboard.

If no alerts:
"No active lawsuits found. We're watching." with green pulsing dot.

If alerts:
- summary bar: watching count, active cases, last checked
- sort by days_remaining ascending
- show CaseCard for each alert
- Check Now button for all watches

Urgency colors:
- <=3 days CRITICAL red
- <=7 days URGENT orange
- <=14 days WARNING yellow
- >14 days MONITOR blue
```

### F5 — Case UX + Risk/Pattern Components

```text
Build:
- CaseCard.tsx
- AnswerModal.tsx
- RiskScoreCard.tsx
- PatternAlert.tsx

CaseCard shows:
- case number, filing date, plaintiff, amount
- deadline countdown
- limitations status
- collector win rate
- default risk score if available
- pattern badge if available
- buttons: Get Answer Form, Find Legal Aid

AnswerModal shows:
- prefilled answer text
- window.print() download shortcut
- legal aid list
- Miro board link
- disclaimer: "This is not legal advice. Contact a licensed attorney."
```

### F6 — Miro Service

```text
In backend/services/miro_service.py implement create_case_board(case: CourtCase, alert: Alert) -> str.

Use MIRO_ACCESS_TOKEN and MIRO_BOARD_ID.
Create:
- case frame
- red deadline sticky
- timeline: Filed -> Deadline -> Hearing
- checklist sticky
- strongest defense sticky
- risk/pattern sticky if available

Return frame URL. If Miro fails, return empty string and log; do not crash alert generation.
```

## Member 3 — Algorithms + Risk

### A1 — Deadline Calculator

```text
Replace backend/services/deadline_calculator.py with the dataclass contract.

Implement DeadlineResult and calculate_deadline().
Rules:
- Justice Court: 14 days from service_date
- District/County: next Monday after 20 days from service_date
- If service_date is None: filing_date + 3 days
- urgency thresholds: <=3 CRITICAL, <=7 URGENT, <=14 WARNING, else MONITOR

Add backend/services/test_deadline.py with pytest coverage for court types and urgency levels.
```

### A2 — Statute Of Limitations

```text
In backend/services/limitations_checker.py implement LimitationsResult and check_statute_of_limitations().

Texas consumer debt rule: 4 years.
Clock starts at last_payment_date if present, else debt_origin_date.

Defense strength:
- STRONG: elapsed > 4.0
- BORDERLINE: 3.5 < elapsed <= 4.0
- UNLIKELY: 3.0 < elapsed <= 3.5
- NONE: elapsed <= 3.0

Add pytest tests for every defense strength.
```

### A3 — Collector Scorer

```text
In backend/services/collector_scorer.py implement CollectorProfile and score_collector().

Inputs: plaintiff_name and historical cases.
Calculate:
- total cases
- default_win_rate
- avg_claim_amount
- common_errors
- threat_level

Detect:
- improper service in >10% of notes
- suspicious round amounts
- clustered filing dates

Add pytest tests for HIGH, MEDIUM, LOW threat levels.
```

### A4 — Property Lookup

```text
In backend/services/property_lookup.py implement:
- normalize_address(raw_address: str) -> str
- async lookup_owner(address: str, county: str = "travis") -> dict | None

Use TCAD public API for Travis:
https://stage.traviscad.org/api/v1/search?address={address}

Return owner_name, owner_mailing_address, parcel_id, legal_description.
Never crash; return None if not found or unavailable.
Add tests for address normalization and mocked TCAD response parsing.
```

### A5 — Demo Risk + Pattern Layer

```text
Create:
- backend/layer2_risk/feature_engineer.py
- backend/layer2_risk/risk_model.py
- backend/layer3_patterns/pattern_detector.py
- backend/models/pattern.py

Use deterministic heuristic scoring first:
- justice court increases risk
- high collector win rate increases risk
- fewer days remaining increases risk
- time-barred debt lowers plaintiff strength but raises alert importance

Pattern detector should flag:
- bulk filing days
- same plaintiff filing many cases in a short period
- ZIP clustering if ZIP data exists

Return simple dicts compatible with frontend.
```

## Integration Checkpoints

### Checkpoint 1 — Backend Skeleton Works

```bash
cd backend
python3 -m py_compile agents/court_monitor.py services/court_scraper.py services/deadline_calculator.py
```

Expected: no syntax errors.

### Checkpoint 2 — Algorithm Tests Pass

```bash
cd backend
pytest services/test_deadline.py services/test_limitations.py services/test_collector_scorer.py -v
```

Expected: all tests pass.

### Checkpoint 3 — Full Local Flow

```bash
cd backend
uvicorn main:app --reload
```

```bash
cd frontend
npm run dev
```

```bash
curl -X POST http://localhost:8000/watch \
  -H "Content-Type: application/json" \
  -d '{"type":"name","value":"John Smith","county":"harris","email":"test@test.com"}'
```

Expected: `cases_found >= 0`, no uncaught errors.

## Cut Scope If Time Gets Tight

Keep:
- Name Watch
- deadline calculation
- simple alert
- dashboard
- MCP tools
- one Miro board update

Cut or fake with clearly labeled demo data:
- full Texas SOS LLC graph
- trained GradientBoosting model
- address watch beyond Travis
- email SMTP
- PDF generation beyond `window.print()`
