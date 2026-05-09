# TxAlert ⚖️
### *"The court was always watching you. Now you can watch back."*

> Built at the AITX × Codex Hackathon — May 8–10, 2025 · Austin, TX

---

## What Is TxAlert?

TxAlert is an autonomous agent that monitors Texas civil court filings 24/7 and alerts regular Texans before they lose lawsuits by doing nothing.

In Texas, debt collectors win **70% of cases by default** — not because defendants lose on the merits, but because they never knew they were sued. TxAlert fixes the information gap using 5 technical layers: entity resolution, ML risk prediction, ownership graph traversal, temporal pattern detection, and autonomous alert generation.

---

## The Problem

- **3 million** debt collection lawsuits filed against Texans since 2012
- **70%** end in default — defendant never showed up
- **90%** of debt collectors have a lawyer. Most defendants do not
- **14 days** to respond in Texas Justice Court before automatic loss
- **$198,000** — what a San Marcos homeowner lost to a secret judgment

---

## 5-Layer Technical Architecture

```
LAYER 0 — Data Ingestion
  court_scraper.py → Harris + Travis County Odyssey portals ✅ DONE
  property_lookup.py → TCAD property to owner cross-reference

LAYER 1 — Entity Resolution Engine  
  entity_resolver.py → fuzzy NLP name matching across variations
  llc_graph.py → Texas SOS corporate ownership graph traversal
  Result: "LVNV Funding LLC" = "Resurgent Capital" = 47 subsidiaries

LAYER 2 — Default Risk Model
  feature_engineer.py → 10-feature vector per case
  risk_model.py → scikit-learn GradientBoostingClassifier
  Output: 0-100 probability defendant loses by default

LAYER 3 — Pattern Detection
  pattern_detector.py → time series anomaly detection on filings
  Detects: bulk filing days, holiday targeting, ZIP predation
  Output: anomaly_score + plain English pattern description

LAYER 4 — Alert Generation
  defense_detector.py → deterministic Texas law rule engine
  alert_generator.py → plain English alert + Answer form
  miro_service.py → live visual Miro board per case
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Next.js 14 + Tailwind CSS |
| Backend | FastAPI Python 3.11 |
| Database | Supabase PostgreSQL |
| ML | scikit-learn GradientBoostingClassifier |
| NLP | spaCy + TF-IDF |
| Graph | NetworkX |
| LLM | OpenAI gpt-4.1 (alert text only) |
| Court Data | Harris + Travis County Odyssey portals |
| Property | TCAD public API |
| Corporate | Texas SOS public filings |
| MCP | modelcontextprotocol/python-sdk |
| Visual | Miro REST API + Miro MCP |

---

## Project Structure

```
txalert/
├── backend/
│   ├── agents/
│   │   ├── court_monitor.py
│   │   ├── case_analyzer.py
│   │   └── alert_generator.py
│   ├── layer1_entity/
│   │   ├── entity_resolver.py
│   │   └── llc_graph.py
│   ├── layer2_risk/
│   │   ├── feature_engineer.py
│   │   └── risk_model.py
│   ├── layer3_patterns/
│   │   └── pattern_detector.py
│   ├── services/
│   │   ├── court_scraper.py         ✅ DONE
│   │   ├── deadline_calculator.py
│   │   ├── limitations_checker.py
│   │   ├── collector_scorer.py
│   │   ├── property_lookup.py
│   │   ├── miro_service.py
│   │   └── legal_aid_finder.py
│   ├── mcp/server.py
│   ├── models/case.py               ✅ DONE
│   └── main.py                      ✅ DONE
├── frontend/src/
│   ├── components/
│   │   ├── WatchForm.tsx
│   │   ├── AlertDashboard.tsx
│   │   ├── CaseCard.tsx
│   │   └── AnswerModal.tsx
│   ├── lib/api.ts
│   └── store/alertStore.ts
├── AGENTS.md
└── README.md
```

---

## Tracks

**Texas Open Data** — Court records, TCAD property, Texas SOS filings. MCP server + agent skill both shipped = especially competitive.

**Agents Track** — Monitors continuously, resolves entities, predicts risk, detects patterns, generates defenses, alerts autonomously. Zero human input required.

---

## Patent Bounty

Entity resolution + default risk prediction algorithm for defendant protection = novel method. Submit deepinvent.ai tonight. $500 cash.

---

## Demo — Sunday

1. Enter name → entity resolver finds all LLC variations
2. Risk score appears: "87% chance of losing"
3. Statute check: "Debt from 2019 — may be time-barred"
4. Pattern: "Collector targets low-income ZIP codes"
5. Answer form pre-filled and ready
6. Miro board shows full case intelligence

*"The court system notified lawyers in October 2025. We built the version for everyone else."*

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
