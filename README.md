# TxAlert ⚖️
### *"The court was always watching you. Now you can watch back."*

> Built at the AITX × Codex Hackathon — May 8–10, 2025 · Austin, TX

---

## What Is TxAlert?

TxAlert is an autonomous agent that monitors Texas civil court filings 24/7 and alerts regular Texans before they lose lawsuits by doing nothing.

In Texas, debt collectors win **70% of cases by default** — not because defendants lose on the merits, but because defendants never knew they were sued. A debt collector files a lawsuit, the person is never properly served, the 14-day deadline passes, and a judge enters a default judgment. Bank account frozen. Wages garnished. Credit destroyed. All preventable with a single alert.

TxAlert fixes the information gap. The court filings were always public. Nobody was watching them for regular people.

---

## The Problem — By The Numbers

- **3 million** debt collection lawsuits filed against Texans since 2012
- **70%** end in default judgment — defendant never showed up
- **90%** of debt collectors have a lawyer. Most defendants do not.
- **14 days** — how long a Texas Justice Court defendant has to respond
- **$0** — what it costs to file an Answer and prevent automatic loss
- **$198,000** — what a San Marcos homeowner lost to a secret code enforcement judgment he never knew existed

The data to prevent this was always public. No tool was watching it for the people who needed it most.

---

## What TxAlert Builds

### Two Watch Modes — One Product

**Name Watch**
Enter your name and county. TxAlert monitors Texas Justice Court and civil court filings daily. If a debt collector, city, or anyone else files a lawsuit naming you — you get an alert before your deadline.

**Address Watch**
Enter your property address. TxAlert monitors court filings cross-referenced against public property records. If a code enforcement action, lien, or civil judgment is filed against your property — you get an alert before you lose by default.

### What the Agent Does Autonomously

```
1. Monitors Harris County + Travis County court filings daily
2. Cross-references new filings against watched names and addresses
3. When match found — calculates deadline automatically
   → Justice Court: 14 days from service
   → District Court: 20 days + following Monday
4. Checks statute of limitations automatically
   → "This debt is from 2019 — past Texas's 4-year limit"
5. Flags debt collector win rate
   → "This collector wins 94% of cases where defendants don't respond"
6. Generates pre-filled Answer form specific to the case type
7. Connects to nearest free legal aid organization
8. Updates Miro board with case timeline and action items
9. Sends follow-up reminder at 7 days, 3 days, 1 day before deadline
```

---

## Why This Is Original

Every existing tool waits for the person to come to it:

| Tool | What it does | Problem |
|---|---|---|
| Texas Law Help | Guides for responding to lawsuits | Only helps people who already know |
| SoloSuit | Helps file an Answer | Requires you to know you've been sued |
| Lone Star Legal Aid | Free Answer filing tool | You must already have the case number |
| Re:SearchTX | Court record search | Built for lawyers, requires registration |
| Texas Court Notices (Oct 2025) | Automatic notifications | Attorneys only — not regular people |

**TxAlert is the first tool that finds you before you lose.**

Academic confirmation: A2J Lab's 2025 research explicitly states they are *"aware of no other research"* on proactive outreach to debt collection defendants in Texas.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 + Tailwind CSS |
| Backend | FastAPI (Python 3.11) |
| Database | Supabase (PostgreSQL) |
| Agent Layer | OpenAI Responses API (gpt-4.1) |
| Court Data | Harris County Odyssey Portal + Travis County public records |
| Property Records | TCAD (Travis Central Appraisal District) public API |
| MCP Server | modelcontextprotocol/python-sdk |
| Visual Board | Miro REST API + Miro MCP |
| Alerts | Supabase Realtime + email |

---

## Project Structure

```
txalert/
├── backend/
│   ├── agents/
│   │   ├── court_monitor.py      # Monitors court filings daily
│   │   ├── case_analyzer.py      # Analyzes case type, deadline, defenses
│   │   └── alert_generator.py    # Generates plain English alerts + Answer forms
│   ├── services/
│   │   ├── court_scraper.py      # Queries Harris + Travis court portals
│   │   ├── property_lookup.py    # TCAD property → owner cross-reference
│   │   ├── deadline_calculator.py # Calculates response deadlines
│   │   ├── limitations_checker.py # Checks 4-year statute of limitations
│   │   ├── legal_aid_finder.py   # Nearest free legal aid by ZIP
│   │   └── miro_service.py       # Updates Miro board
│   ├── mcp/
│   │   └── server.py             # MCP server exposing 6 tools
│   ├── models/
│   │   └── case.py               # Case, Alert, WatchEntry data models
│   └── main.py                   # FastAPI entry point
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── WatchForm.tsx      # Name/address watch setup
│       │   ├── AlertDashboard.tsx # Active alerts with deadlines
│       │   ├── CaseCard.tsx       # Individual case details
│       │   └── AnswerGenerator.tsx # Pre-filled Answer form
│       ├── lib/
│       │   └── api.ts             # API client
│       └── store/
│           └── alertStore.ts      # Zustand global state
├── .agents/
│   └── skills/
│       ├── court-monitor.md       # Codex skill: monitoring loop
│       ├── case-analyzer.md       # Codex skill: case analysis
│       └── alert-generator.md     # Codex skill: alert generation
├── docs/
│   ├── data_schema.md             # Full data models
│   ├── setup.md                   # Installation guide
│   └── team.md                    # Team roles and build plan
├── AGENTS.md                      # Codex navigation guide
└── README.md                      # This file
```

---

## MCP Server Tools

```python
watch_name(name: str, county: str)
# Register a name to watch for civil filings

watch_address(address: str, county: str)
# Register an address to watch for property actions

get_active_cases(watch_id: str)
# Get all open cases for a watched name/address

get_case_deadline(case_id: str)
# Calculate days remaining before default judgment

check_statute_limits(case_id: str)
# Determine if debt is past 4-year Texas limit

find_legal_aid(zip_code: str)
# Get nearest free legal aid organizations
```

---

## Tracks

**Texas Open Data Track** — Harris County and Travis County court records are public Texas data. TCAD property records are public. All data is attributed to source with direct links. MCP server + agent skill both shipped = especially competitive per track rules.

**Agents Track** — The monitoring agent runs continuously without human input. It detects new filings, calculates deadlines, checks defenses, generates forms, and sends alerts — all autonomously. It recovers if data is temporarily unavailable and retries on next cycle.

---

## Social Impact

> *"Debt collectors count on you not knowing you've been sued. We make sure you know."*

- Prevents default judgments for people who had valid defenses they never got to raise
- Specifically protects low-income Texans, immigrants, and elderly residents — the people most likely to be targeted and least likely to know their rights
- Open source — free forever — because the people who need this most cannot pay for it
- Bilingual — English and Spanish — because Texas Justice Court publishes Spanish forms

---

## Demo Flow (Sunday — Hack Fair)

1. Open TxAlert on laptop
2. Enter a real name — show a real Harris County debt lawsuit found from public records
3. Show the 14-day deadline countdown
4. Show automatic statute of limitations check: *"This debt is from 2019 — may be time-barred"*
5. Show pre-filled Answer form generated for this specific case
6. Show Miro board: case timeline, action checklist, legal aid locations
7. Enter a real San Marcos address — show the code enforcement judgment that cost a homeowner $198K
8. Show what the alert would have looked like 20 days earlier

**Pitch:** *"The court system notified lawyers in October 2025. We built the version for everyone else."*

---

## Patent Bounty

The **deadline prediction + defense detection algorithm** — calculating response urgency from case type, jurisdiction, filing date, and statute of limitations — is a novel method for protecting defendants in civil litigation. Submit to deepinvent.ai for the $500 patent bounty before Sunday.

---

## Disclaimer

TxAlert provides information from public court records to help people understand their legal situation. It does not provide legal advice. Users should consult a licensed attorney for legal guidance. Every case alert includes a referral to free legal aid.

---

*TxAlert — Built in 48 hours. Because justice shouldn't depend on whether you checked the right website.*
